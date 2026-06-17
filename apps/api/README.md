# Sudoke API

FastAPI backend for the Sudoke competitive social sudoku platform.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

## Local Development

```bash
# From apps/api/
cp .env.example .env

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run the dev server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Compose

```bash
# From the repo root (assumes docker-compose.yml exists)
docker compose up api
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## API Docs

Once running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/v1/health
