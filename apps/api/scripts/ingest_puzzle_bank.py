"""Ingest puzzles from the Sudoku Exchange bank into the database.

This script is the launch-gate workhorse for **Epic 5 — Puzzle Ops &
Content Pipeline** (PRD §10.2 / §21):

1. Parses raw rows from ``data/raw/sudoku_exchange/*.txt`` (format
   ``<hash> <81-digit-givens> <rating>``).
2. Validates each puzzle with the same ``src.sudoku`` engine the API
   uses (unique solution, clue count, no-guessing check).
3. Inserts into ``puzzles`` as ``needs_review``, then auto-approves
   (the source is CC0 / public-domain so review can be deferred to
   spot checks).
4. Optionally bulk-schedules approved puzzles into ``daily_puzzles``
   on consecutive UTC dates, or into the launch weekly rotation
   (Mon/Tue easy, Wed/Thu medium, Fri/Sat/Sun hard) with
   ``--weekly-rotation`` when multiple difficulty banks are loaded.

Idempotent: re-running with the same input file skips puzzles that are
already in the database, and skips dates that already have a scheduled
puzzle.

Usage (SQLite dev):

    DATABASE_URL=sqlite+aiosqlite:///./dev.db \\
    python -m scripts.ingest_puzzle_bank \\
        --source data/raw/sudoku_exchange/easy.txt \\
        --difficulty easy \\
        --limit 120 \\
        --schedule \\
        --weekly-rotation \\
        --schedule-start 2026-06-23

The script creates tables on first run via ``Base.metadata.create_all``
when the target DB has none yet, so it works against a brand-new SQLite
file without needing Alembic.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from src import sudoku
from src.db.base import Base
from src.db.session import async_session_factory, engine
from src.models import (
    AdminAuditLog,
    DailyPuzzle,
    DailyPuzzleStatus,
    Puzzle,
    PuzzleStatus,
    User,
    UserRole,
)
from src.models.puzzles import PuzzleDifficulty
from src.services.puzzles import _activation_window

# `src.db.session` sets `echo=True` in development, which makes SQLAlchemy
# print every query. That noise drowns the ingestion summary, so we
# disable it here at the engine + sync-engine level.
engine.echo = False
engine.sync_engine.echo = False

DifficultyName = Literal["easy", "medium", "hard", "expert"]

# Sudoku Exchange ratings are a continuous 1.0-4+ scale. These ranges
# define a roomy estimated solve-time envelope per difficulty bucket so
# the daily countdown UI has something realistic to show.
ESTIMATED_RANGE_SECONDS: dict[DifficultyName, tuple[int, int]] = {
    "easy": (180, 480),
    "medium": (360, 900),
    "hard": (600, 1500),
    "expert": (900, 2400),
}

WEEKLY_ROTATION_WEEKDAYS: dict[DifficultyName, set[int]] = {
    "easy": {0, 1},
    "medium": {2, 3},
    "hard": {4, 5, 6},
    "expert": set(),
}

DEFAULT_SOURCE_NAME = "Sudoku Exchange Puzzle Bank"
DEFAULT_SOURCE_LICENSE = "Public Domain (CC0)"
DEFAULT_ADMIN_AUTH_ID = "admin-dev"


@dataclass(frozen=True)
class RawPuzzleRow:
    source_hash: str
    givens: str
    source_rating: float
    source_file: str
    source_line: int


@dataclass
class IngestStats:
    seen: int = 0
    inserted: int = 0
    skipped_existing: int = 0
    rejected_invalid: int = 0
    approved: int = 0
    scheduled: int = 0
    skipped_dates: int = 0


def parse_source_line(line: str) -> tuple[str, str, float] | None:
    """Parse one ``<hash> <givens> <rating>`` row, ``None`` for blanks."""

    stripped = line.strip()
    if not stripped:
        return None
    parts = stripped.split()
    if len(parts) != 3:
        raise ValueError(f"Expected 3 columns, got {len(parts)}: {stripped!r}")
    src_hash, givens, rating = parts
    if len(givens) != 81 or any(ch not in "0123456789." for ch in givens):
        raise ValueError(f"Bad givens: {givens!r}")
    return src_hash, givens.replace(".", "0"), float(rating)


def iter_source_file(path: Path, *, limit: int) -> Iterator[RawPuzzleRow]:
    """Stream `limit` rows from a puzzle bank source file."""

    with path.open("r", encoding="utf-8") as f:
        emitted = 0
        for line_no, line in enumerate(f, start=1):
            if limit > 0 and emitted >= limit:
                return
            parsed = parse_source_line(line)
            if parsed is None:
                continue
            src_hash, givens, rating = parsed
            yield RawPuzzleRow(
                source_hash=src_hash,
                givens=givens,
                source_rating=rating,
                source_file=path.name,
                source_line=line_no,
            )
            emitted += 1


async def ensure_schema() -> None:
    """Create tables on first run against an empty DB (SQLite dev only)."""

    def _has_tables(sync_conn: object) -> bool:
        return bool(inspect(sync_conn).get_table_names())

    async with engine.begin() as conn:
        has_tables = await conn.run_sync(_has_tables)
        if not has_tables:
            await conn.run_sync(Base.metadata.create_all)


async def ensure_admin_user(
    session: AsyncSession, *, auth_id: str
) -> User:
    """Materialize an admin User row that owns the audit trail."""

    existing = await session.execute(
        select(User).where(User.auth_provider_id == auth_id)
    )
    user = existing.scalar_one_or_none()
    if user is not None:
        if user.role != UserRole.admin:
            user.role = UserRole.admin
        return user
    user = User(
        auth_provider_id=auth_id,
        email=f"{auth_id}@sudoke.local",
        username=auth_id,
        display_name="Puzzle Ingestion Bot",
        role=UserRole.admin,
        is_guest=False,
    )
    session.add(user)
    await session.flush()
    return user


def _build_notes(row: RawPuzzleRow) -> str:
    return (
        f"sudoku_exchange:{row.source_hash} "
        f"rating={row.source_rating} "
        f"line={row.source_line}"
    )


async def _existing_puzzle_ids(
    session: AsyncSession, givens_list: list[str]
) -> set[str]:
    """Return the subset of givens strings that already exist in the DB."""

    if not givens_list:
        return set()
    result = await session.execute(
        select(Puzzle.givens).where(Puzzle.givens.in_(givens_list))
    )
    return {row[0] for row in result.all()}


async def import_and_approve(
    session: AsyncSession,
    rows: list[RawPuzzleRow],
    *,
    difficulty: DifficultyName,
    actor: User,
    stats: IngestStats,
) -> list[Puzzle]:
    """Import + auto-approve the given puzzle rows, skipping duplicates."""

    pre_existing = await _existing_puzzle_ids(
        session, [r.givens for r in rows]
    )

    min_secs, max_secs = ESTIMATED_RANGE_SECONDS[difficulty]
    inserted: list[Puzzle] = []

    for row in rows:
        stats.seen += 1
        if row.givens in pre_existing:
            stats.skipped_existing += 1
            continue

        givens_grid = sudoku.parse_grid(row.givens)
        result = sudoku.validate_puzzle(givens_grid)
        if not result.ok or result.solution is None:
            stats.rejected_invalid += 1
            continue

        now = datetime.now(timezone.utc)
        puzzle = Puzzle(
            givens=row.givens,
            solution=sudoku.serialize_grid(list(result.solution)),
            difficulty=PuzzleDifficulty(difficulty),
            status=PuzzleStatus.approved,
            estimated_min_seconds=min_secs,
            estimated_max_seconds=max_secs,
            clue_count=result.clue_count,
            source=DEFAULT_SOURCE_NAME,
            license=DEFAULT_SOURCE_LICENSE,
            notes=_build_notes(row),
            reviewer_id=actor.id,
            reviewed_at=now,
            review_notes=(
                "Auto-approved from sudoku-exchange CC0 bank "
                "(unique solution + no-guess validated)."
            ),
        )
        session.add(puzzle)
        await session.flush()
        inserted.append(puzzle)
        stats.inserted += 1
        stats.approved += 1

        session.add(
            AdminAuditLog(
                actor_user_id=actor.id,
                action="puzzle.ingested",
                target_type="puzzle",
                target_id=str(puzzle.id),
                payload={
                    "source_hash": row.source_hash,
                    "source_rating": row.source_rating,
                    "difficulty": difficulty,
                    "auto_approved": True,
                },
            )
        )

    return inserted


async def schedule_puzzles(
    session: AsyncSession,
    puzzles: list[Puzzle],
    *,
    start_date: date,
    actor: User,
    stats: IngestStats,
    allowed_weekdays: set[int] | None = None,
) -> list[DailyPuzzle]:
    """Append approved puzzles to the daily calendar, one per date.

    Skips dates already scheduled (idempotent re-run friendly).
    If `allowed_weekdays` is set, only schedules onto those UTC weekdays
    (`date.weekday()`: Mon=0 ... Sun=6).
    """

    if not puzzles:
        return []
    if allowed_weekdays is not None and not allowed_weekdays:
        raise ValueError("allowed_weekdays must contain at least one weekday")

    taken_dates = await session.execute(
        select(DailyPuzzle.scheduled_for).where(
            DailyPuzzle.scheduled_for >= start_date
        )
    )
    taken: set[date] = {row[0] for row in taken_dates.all()}

    scheduled: list[DailyPuzzle] = []
    cursor = start_date
    queue = list(puzzles)
    while queue:
        if allowed_weekdays is not None and cursor.weekday() not in allowed_weekdays:
            cursor += timedelta(days=1)
            continue
        if cursor in taken:
            stats.skipped_dates += 1
            cursor += timedelta(days=1)
            continue
        puzzle = queue.pop(0)
        activate_at, finalize_at = _activation_window(cursor)
        daily = DailyPuzzle(
            puzzle_id=puzzle.id,
            scheduled_for=cursor,
            activate_at=activate_at,
            finalize_at=finalize_at,
            status=DailyPuzzleStatus.scheduled,
        )
        session.add(daily)
        scheduled.append(daily)
        stats.scheduled += 1
        cursor += timedelta(days=1)

    await session.flush()
    session.add(
        AdminAuditLog(
            actor_user_id=actor.id,
            action="daily.bulk_scheduled",
            target_type="daily_puzzles",
            target_id=None,
            payload={
                "count": len(scheduled),
                "start_date": start_date.isoformat(),
                "allowed_weekdays": (
                    sorted(allowed_weekdays) if allowed_weekdays is not None else None
                ),
            },
        )
    )
    return scheduled


async def run(
    *,
    source: Path,
    difficulty: DifficultyName,
    limit: int,
    do_schedule: bool,
    schedule_start: date,
    weekly_rotation: bool,
    admin_auth_id: str,
) -> IngestStats:
    stats = IngestStats()

    await ensure_schema()

    async with async_session_factory() as session:  # type: AsyncSession
        actor = await ensure_admin_user(session, auth_id=admin_auth_id)
        await session.commit()

        rows = list(iter_source_file(source, limit=limit))
        if not rows:
            print("No rows parsed from source file — nothing to do.")
            return stats

        async with session.begin():
            inserted = await import_and_approve(
                session,
                rows,
                difficulty=difficulty,
                actor=actor,
                stats=stats,
            )
            if do_schedule and inserted:
                allowed_weekdays = (
                    WEEKLY_ROTATION_WEEKDAYS[difficulty] if weekly_rotation else None
                )
                await schedule_puzzles(
                    session,
                    inserted,
                    start_date=schedule_start,
                    actor=actor,
                    stats=stats,
                    allowed_weekdays=allowed_weekdays,
                )

    return stats


def _arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ingest puzzles into the DB.")
    p.add_argument(
        "--source",
        type=Path,
        default=Path("data/raw/sudoku_exchange/easy.txt"),
    )
    p.add_argument(
        "--difficulty",
        choices=list(ESTIMATED_RANGE_SECONDS.keys()),
        default="easy",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max puzzles to read (0 = no limit).",
    )
    p.add_argument(
        "--schedule",
        action="store_true",
        help="Also append to the daily_puzzles calendar.",
    )
    p.add_argument(
        "--schedule-start",
        type=date.fromisoformat,
        default=date.today(),
        help="UTC date for the first scheduled daily (YYYY-MM-DD).",
    )
    p.add_argument(
        "--weekly-rotation",
        action="store_true",
        help=(
            "When scheduling, place easy on Mon/Tue, medium on Wed/Thu, "
            "and hard on Fri/Sat/Sun UTC dates."
        ),
    )
    p.add_argument(
        "--admin-auth-id",
        default=DEFAULT_ADMIN_AUTH_ID,
        help="auth_provider_id of the admin User row to attribute audits to.",
    )
    return p


async def _amain(args: argparse.Namespace) -> int:
    if not args.source.exists():
        print(f"Source file not found: {args.source}")
        return 2

    try:
        stats = await run(
            source=args.source,
            difficulty=args.difficulty,
            limit=args.limit,
            do_schedule=args.schedule,
            schedule_start=args.schedule_start,
            weekly_rotation=args.weekly_rotation,
            admin_auth_id=args.admin_auth_id,
        )
    finally:
        await engine.dispose()

    print("--- Ingestion summary ---")
    print(f"  Seen:             {stats.seen}")
    print(f"  Inserted:         {stats.inserted}")
    print(f"  Skipped existing: {stats.skipped_existing}")
    print(f"  Rejected invalid: {stats.rejected_invalid}")
    print(f"  Approved:         {stats.approved}")
    print(f"  Scheduled:        {stats.scheduled}")
    print(f"  Skipped dates:    {stats.skipped_dates}")
    return 0


def main() -> None:
    parser = _arg_parser()
    args = parser.parse_args()
    exit_code = asyncio.run(_amain(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
