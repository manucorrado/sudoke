# AGENTS.md

## Cursor Cloud specific instructions

Sudoke is a pnpm + Turborepo monorepo. Standard commands live in `README.md`, the root
`package.json` scripts, and `apps/api/README.md`. The notes below are the non-obvious
caveats specific to running it in this environment.

### Services & how to run them
The update script installs dependencies but does NOT start services. Start them yourself.

| Service | Required | Port | How to run |
|---------|----------|------|------------|
| PostgreSQL 16 | yes | 5432 | `sudo pg_ctlcluster 16 main start` |
| Redis 7 | yes | 6379 | `sudo redis-server /etc/redis/redis.conf --daemonize yes` |
| API (FastAPI) | yes | 8000 | from `apps/api`: `source .venv/bin/activate && uvicorn src.main:app --reload --host 0.0.0.0 --port 8000` |
| Mobile (Expo web) | yes | 8081 | `pnpm dev:mobile:web` (primary user-facing app) |
| Admin (Next.js) | optional | 3001 | `pnpm dev:admin` |

- Postgres/Redis are installed natively via apt (not Docker, since Docker isn't available here)
  and are NOT auto-started — start them after each VM boot. Postgres uses role/password
  `postgres`/`postgres` and database `sudoke`; TCP password auth on `127.0.0.1` works out of the box.
- `pnpm dev:api` does NOT work: `apps/api` has no `package.json` and isn't a pnpm/turbo workspace.
  Run the API directly with `uvicorn` inside its venv at `apps/api/.venv`.

### Database schema (important gotcha)
The Alembic migration `0001_baseline` is broken on Postgres: it manually creates the `user_role`
enum and then `create_table` re-emits `CREATE TYPE`, raising `DuplicateObjectError`, so `alembic
upgrade head` fails. To provision the schema on a fresh Postgres DB, create the tables from the ORM
metadata and then stamp Alembic. From `apps/api` with the venv active:

```bash
python - <<'PY'
import asyncio
from src.db.base import Base
from src.db.session import engine
from src import models  # noqa: F401  registers ORM mappers

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(main())
PY
alembic stamp head
```

The Postgres data dir persists in the VM snapshot, so this is typically only needed once.

The pytest suite does NOT need Postgres/Redis — `tests/conftest.py` uses in-memory SQLite
(`aiosqlite`) and mocks auth.

### pnpm layout (do not change)
- `.npmrc` sets `node-linker=hoisted`. This is REQUIRED — Expo/Metro cannot resolve modules
  (`react`, `@babel/runtime`, ...) under pnpm's default isolated layout. Keep it.
- `package.json` `pnpm.overrides` pins `@types/react`/`@types/react-dom` to v18 to avoid a
  React 18 (mobile/Expo) vs 19 (admin) type clash in the flat `node_modules`.
- After changing dependencies, restart Metro and clear its caches:
  `rm -rf apps/mobile/.expo apps/mobile/node_modules/.cache` then `pnpm dev:mobile:web`.

### Lint / test / build status
- `pnpm lint`, `pnpm typecheck`, `pnpm test` are green across all packages.
- API tests: `cd apps/api && source .venv/bin/activate && pytest`.
- `ruff check` on `apps/api` reports many pre-existing lint findings (ruff is not wired into CI).
- `pnpm build` builds `sudoku-core` fine, but the optional **admin** app's `next build` fails at
  prerender (`Cannot read properties of null (reading 'useContext')`) because admin pins React 19
  while the rest of the repo pins React 18, which only conflicts in the hoisted `node_modules`.
  Admin lint/typecheck still pass. Admin is not needed for the core gameplay flow.

### Mobile app notes
- Guest-first: the **Play** (Casual) tab is fully client-side via `@sudoke/sudoku-core` and works
  with no backend. The **Today** tab calls `/api/v1/daily/current`, which returns nothing until a
  daily puzzle is seeded via the admin endpoints.
- A red `SecureStore` error toast appears on first web load (Clerk's `expo-secure-store` token
  cache on web). It is harmless and does not block gameplay.
- The API base URL is hardcoded to `http://localhost:8000/api/v1` in `apps/mobile/src/lib/api.ts`.
