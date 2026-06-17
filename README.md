# Sudoke — Competitive Social Sudoku

A competitive daily Sudoku app with ranked play, social challenges, and leaderboards.

## Monorepo Structure

```
apps/
  mobile/     — Expo React Native app (iOS, Android, Web)
  api/        — FastAPI backend
  admin/      — Next.js admin dashboard
packages/
  sudoku-core/ — Shared Sudoku game logic (TypeScript)
```

## Prerequisites

- **Node.js** 20+ (see `.nvmrc`)
- **pnpm** 9+ (`corepack enable && corepack prepare pnpm@9.15.4 --activate`)
- **Python** 3.11+ (for the API)
- **Docker** & Docker Compose (for local Postgres + Redis)

## Quick Start

### 1. Install dependencies

```bash
pnpm install
```

### 2. Start infrastructure (Postgres + Redis)

```bash
docker compose up -d postgres redis
```

### 3. Set up the API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
```

### 4. Run the API

```bash
# From apps/api with venv activated
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Or from the repo root:

```bash
pnpm dev:api
```

### 5. Run the mobile app

```bash
# iOS/Android simulator
pnpm dev:mobile

# Web (for agent development)
pnpm dev:mobile:web
```

### 6. Run the admin dashboard

```bash
pnpm dev:admin
```

## Development

| Command | Description |
|---------|-------------|
| `pnpm dev:mobile` | Start Expo dev server |
| `pnpm dev:mobile:web` | Start mobile app in browser |
| `pnpm dev:api` | Start FastAPI with hot reload |
| `pnpm dev:admin` | Start admin dashboard |
| `pnpm lint` | Lint all packages |
| `pnpm typecheck` | Type-check all packages |
| `pnpm test` | Run tests across all packages |
| `docker compose up` | Start all services (API + Postgres + Redis) |

## Agent Development

The mobile app supports Expo Web for browser-based development and testing.
Navigate to `/dev/screens` in the web app to access dev/test screen listings.

## Tech Stack

- **Mobile**: Expo (SDK 52), React Native, Expo Router, TanStack Query, Zustand
- **Backend**: FastAPI, SQLAlchemy (async), PostgreSQL, Redis, Alembic
- **Admin**: Next.js 15, React 19
- **Shared**: TypeScript, Zod, Vitest
- **Auth**: Clerk
- **Monitoring**: Sentry
