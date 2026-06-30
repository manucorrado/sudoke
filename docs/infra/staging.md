# Staging Deployability Runbook

This repository contains staging configuration in `render.yaml`, but it does
not create or mutate live Render services. Provision the Blueprint manually in
Render and fill every `sync: false` secret from the staging account.

## Render Staging Stack

- API web service: `sudoke-api-staging`
  - Health check: `/api/v1/health/ready`
  - Release command: `alembic upgrade head`
  - Start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
- Cron job: `sudoke-cron-staging`
  - Schedule: every minute
  - Command: `python -m src.jobs.worker tick`
  - Runs daily activation, attempt timeout, and finalization/rating jobs.
- Data services: `sudoke-postgres-staging`, `sudoke-redis-staging`
- Admin web service: `sudoke-admin-staging`
  - Set `API_BASE_URL` to the staging API `/api/v1` URL.
  - Do not use `ADMIN_AUTH_PROVIDER_ID` outside local development.

Required staging API env:

```sh
ENVIRONMENT=staging
API_V1_PREFIX=/api/v1
CORS_ALLOWED_ORIGINS=https://admin.staging.sudoke.app,http://localhost:8081
CLERK_ISSUER=https://<staging-clerk-issuer>
CLERK_SECRET_KEY=<staging-clerk-secret>
DATABASE_URL=<Render Postgres connection string>
REDIS_URL=<Render Redis connection string>
```

`DATABASE_URL` may be Render's default `postgresql://` URL; the API normalizes
it to SQLAlchemy's asyncpg driver form at startup.

## Mobile Staging Build

Set Expo public env before a preview/staging build:

```sh
EXPO_PUBLIC_ENVIRONMENT=staging
EXPO_PUBLIC_API_BASE_URL=https://api.staging.sudoke.app/api/v1
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=<staging-publishable-key>
EXPO_PUBLIC_CHALLENGE_WEB_BASE_URL=https://staging.sudoke.app/c
```

If `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` is absent, the app keeps guest-first
behavior and the local development bearer-token flow.

## Puzzle Content Cutover

Do not point these commands at production until the production database and
launch day are confirmed.

Staging smoke load:

```sh
cd apps/api
ENVIRONMENT=staging \
DATABASE_URL='<staging-postgres-url>' \
python -m scripts.ingest_puzzle_bank \
  --source data/raw/sudoku_exchange/easy.txt \
  --difficulty easy \
  --limit 120 \
  --schedule \
  --weekly-rotation \
  --schedule-start <staging-start-date>
```

Production cutover, manual and still open:

```sh
cd apps/api
ENVIRONMENT=production \
DATABASE_URL='<production-postgres-url>' \
python -m scripts.ingest_puzzle_bank \
  --source data/raw/sudoku_exchange/<easy|medium|hard>.txt \
  --difficulty <easy|medium|hard> \
  --limit 120 \
  --schedule \
  --weekly-rotation \
  --schedule-start <launch-day>
```

The ingestion pipeline is idempotent for duplicate puzzles and already skips
scheduled dates. With `--weekly-rotation`, run the command once per available
bank using the same launch day: easy fills Monday/Tuesday, medium fills
Wednesday/Thursday, and hard fills Friday/Saturday/Sunday. Expert puzzles
remain excluded from the ranked daily rotation.
