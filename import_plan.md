# Puzzle Import & Scheduling Plan

> **Status:** Easy bank (`data/raw/sudoku_exchange/easy.txt`, 100,000 rows)
> ingested end-to-end via `apps/api/scripts/ingest_puzzle_bank.py` on
> 2026-06-22 — see [`EPIC_PLAN_UPDATED.md`](./EPIC_PLAN_UPDATED.md) Epic 5
> entry for the milestone audit.

## Pipeline overview

```
data/raw/sudoku_exchange/<difficulty>.txt        # Raw CC0 bank (1 puzzle / line)
            │
            ▼
scripts/ingest_puzzle_bank.py                    # Parses, validates, inserts,
            │                                    # auto-approves, schedules.
            ▼
puzzles (status=approved) + daily_puzzles        # Bulk-scheduled, one per day
            │
            ▼
src/jobs/tick.py::run_due_jobs (cron)            # Flips scheduled → active at
            │                                    # the UTC midnight rollover
            ▼
GET /api/v1/daily/current                        # Served to mobile clients
```

## Source bank

| File                                       | Difficulty band | Rows    | Status |
|--------------------------------------------|-----------------|---------|--------|
| `data/raw/sudoku_exchange/easy.txt`        | `easy`          | 100,000 | Ingested |
| `data/raw/sudoku_exchange/medium.txt`      | `medium`        | TBD     | Pending upload |
| `data/raw/sudoku_exchange/hard.txt`        | `hard`          | TBD     | Pending upload |
| `data/raw/sudoku_exchange/diabolical.txt`  | `expert`        | TBD     | Pending upload (excluded from ranked rotation) |

Format: `<source_hash> <81-digit-givens> <source_rating>` per line.

## Running the ingestion script

```bash
# Local SQLite (zero-config, creates tables on first run)
DATABASE_URL='sqlite+aiosqlite:///./dev.db' \
ENVIRONMENT=development \
  apps/api/.venv/bin/python -m scripts.ingest_puzzle_bank \
  --source data/raw/sudoku_exchange/easy.txt \
  --difficulty easy \
  --limit 120 \
  --schedule \
  --schedule-start "$(date -u +%F)"
```

**Production (Postgres):** set `DATABASE_URL` to the prod connection
string, then run the same command. The script is idempotent — re-runs
skip puzzles that are already in the DB and dates that already have a
scheduled puzzle.

### Flags

| Flag                | Default                                 | Purpose |
|---------------------|-----------------------------------------|---------|
| `--source`          | `data/raw/sudoku_exchange/easy.txt`     | Path to the raw bank file. |
| `--difficulty`      | `easy`                                  | Maps to the `PuzzleDifficulty` enum and the estimated solve-time range. |
| `--limit`           | `100`                                   | Max rows to read (0 = no limit). |
| `--schedule`        | off                                     | Also bulk-append to `daily_puzzles`. |
| `--schedule-start`  | today (UTC)                             | First date to assign. Subsequent puzzles take the next free date (skipping anything already booked). |
| `--admin-auth-id`   | `admin-dev`                             | `users.auth_provider_id` to attribute audit entries to. Auto-created with role=`admin` on first run. |

## Validation guarantees

Every imported puzzle is run through `src.sudoku.validate_puzzle`, which
matches the client-side engine in `packages/sudoku-core`:

1. Length / character set check (81 cells, digits or blank).
2. `MIN_CLUES = 17` enforced.
3. Solver finds exactly **one** solution (the rejection reason is
   surfaced in the summary as `rejected_invalid`).
4. The computed canonical solution is persisted alongside the givens
   so the API never needs to solve at request time.

Approved puzzles are tagged with `source="Sudoku Exchange Puzzle Bank"`
and `license="Public Domain (CC0)"`, satisfying Epic 5's licensing
exit criterion.

## Launch-gate checklist

- [x] ≥90 approved puzzles in the inventory (admin dashboard "Approved
      inventory" tile shows `100 / 90 (launch goal)`).
- [x] ≥90 dates scheduled in `daily_puzzles` for the launch window.
- [x] Cron (`src/jobs/tick.py`) activates the next day's puzzle at UTC
      midnight and finalizes ratings after each window closes.
- [ ] Run ingestion against production Postgres on launch eve.
- [ ] Ingest medium + hard banks (capacity already exists in the script).
- [ ] Add Mon-Easy … Sun-Hard rotation in the bulk-schedule step.
