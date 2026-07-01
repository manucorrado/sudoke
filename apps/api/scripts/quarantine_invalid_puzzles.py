"""Audit and quarantine invalid persisted puzzles.

Dry-run by default. Pass ``--apply`` to remove invalid puzzles from app
circulation by cancelling linked daily rows and marking the puzzle rejected.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.db.session import async_session_factory, engine
from src.models import DailyPuzzle, Puzzle
from src.models.puzzles import DailyPuzzleStatus, PuzzleStatus
from src.services.puzzles import validate_stored_puzzle

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class InvalidPuzzle:
    puzzle: Puzzle
    issues: tuple[str, ...]


ACTIVE_DAILY_STATUSES = {
    DailyPuzzleStatus.scheduled,
    DailyPuzzleStatus.active,
    DailyPuzzleStatus.finalizing,
}


async def find_invalid_puzzles(session: AsyncSession) -> list[InvalidPuzzle]:
    result = await session.execute(select(Puzzle).order_by(Puzzle.created_at.asc()))
    invalid: list[InvalidPuzzle] = []
    for puzzle in result.scalars():
        issues = validate_stored_puzzle(puzzle)
        if issues:
            invalid.append(InvalidPuzzle(puzzle=puzzle, issues=tuple(issues)))
    return invalid


async def quarantine_invalid_puzzles(
    session: AsyncSession,
    invalid: list[InvalidPuzzle],
) -> tuple[int, int]:
    puzzle_ids = [entry.puzzle.id for entry in invalid]
    if not puzzle_ids:
        return 0, 0

    daily_result = await session.execute(
        select(DailyPuzzle).where(DailyPuzzle.puzzle_id.in_(puzzle_ids))
    )
    cancelled_dailies = 0
    for daily in daily_result.scalars():
        if daily.status in ACTIVE_DAILY_STATUSES:
            daily.status = DailyPuzzleStatus.cancelled
            cancelled_dailies += 1

    rejected_puzzles = 0
    for entry in invalid:
        if entry.puzzle.status != PuzzleStatus.rejected:
            entry.puzzle.status = PuzzleStatus.rejected
            entry.puzzle.review_notes = "Rejected by invalid-puzzle quarantine."
            rejected_puzzles += 1

    await session.flush()
    return rejected_puzzles, cancelled_dailies


async def run(*, apply: bool) -> int:
    async with async_session_factory() as session:
        invalid = await find_invalid_puzzles(session)
        print(f"Invalid puzzles: {len(invalid)}")
        for entry in invalid:
            print(
                f"- puzzle_id={entry.puzzle.id} "
                f"status={entry.puzzle.status.value} "
                f"difficulty={entry.puzzle.difficulty.value}"
            )
            for issue in entry.issues:
                print(f"  issue: {issue}")

        if not apply:
            print("Dry run only. Re-run with --apply to quarantine invalid puzzles.")
            return 0

        rejected, cancelled = await quarantine_invalid_puzzles(session, invalid)
        await session.commit()
        print(f"Rejected puzzles: {rejected}")
        print(f"Cancelled daily rows: {cancelled}")
        return 0


async def _amain(*, apply: bool) -> int:
    try:
        return await run(apply=apply)
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit invalid persisted puzzles.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist quarantine changes. Defaults to dry-run.",
    )
    args = parser.parse_args()
    exit_code = asyncio.run(_amain(apply=args.apply))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
