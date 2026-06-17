"""Seed an active daily puzzle + a 12-player leaderboard cohort.

For manual / end-to-end testing only. Safe to re-run: drops any prior
demo puzzle/cohort first.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import async_session_factory, engine
from src.models import (
    AttemptStatus,
    DailyPuzzle,
    Puzzle,
    PuzzleStatus,
    RankedAttempt,
    User,
    UserRole,
)
from src.models.puzzles import DailyPuzzleStatus, PuzzleDifficulty
from src.services.rating import project_for_attempt
from src.sudoku.engine import parse_grid, serialize_grid, solve

EASY = (
    "530070000"
    "600195000"
    "098000060"
    "800060003"
    "400803001"
    "700020006"
    "060000280"
    "000419005"
    "000080079"
)
EASY_SOL = serialize_grid(solve(parse_grid(EASY)) or [])


async def main() -> None:
    async with async_session_factory() as session:  # type: AsyncSession
        await session.execute(delete(RankedAttempt))
        existing_puzzle = (
            await session.execute(select(Puzzle).where(Puzzle.givens == EASY))
        ).scalar_one_or_none()
        if existing_puzzle is not None:
            await session.execute(
                delete(DailyPuzzle).where(DailyPuzzle.puzzle_id == existing_puzzle.id)
            )
        await session.execute(delete(User).where(User.auth_provider_id.like("demo-%")))
        await session.commit()

        puzzle = existing_puzzle or Puzzle(
            givens=EASY,
            solution=EASY_SOL,
            difficulty=PuzzleDifficulty.medium,
            status=PuzzleStatus.approved,
            estimated_min_seconds=240,
            estimated_max_seconds=600,
            clue_count=30,
            source="seed",
            license="CC0",
        )
        if existing_puzzle is None:
            session.add(puzzle)
        await session.flush()

        now = datetime.now(timezone.utc)
        daily = DailyPuzzle(
            puzzle_id=puzzle.id,
            scheduled_for=date.today(),
            activate_at=now - timedelta(hours=2),
            finalize_at=now + timedelta(hours=22),
            status=DailyPuzzleStatus.active,
        )
        session.add(daily)
        await session.flush()

        for i in range(12):
            user = User(
                auth_provider_id=f"demo-{i}",
                email=f"demo{i}@sudoke.test",
                username=f"demo{i}",
                display_name=f"Demo Player {i}",
                role=UserRole.player,
            )
            session.add(user)
            await session.flush()
            attempt = RankedAttempt(
                user_id=user.id,
                daily_puzzle_id=daily.id,
                status=AttemptStatus.provisional_ranked,
                started_at=now - timedelta(minutes=20),
                submitted_at=now - timedelta(minutes=2, seconds=i * 10),
                mistakes=0 if i < 6 else 1,
                official_duration_ms=300_000 + i * 12_500,
                submitted_grid=EASY_SOL,
            )
            session.add(attempt)
            await session.flush()
            await project_for_attempt(
                session,
                attempt=attempt,
                puzzle_difficulty=PuzzleDifficulty.medium,
            )
        await session.commit()
        print(f"Seeded daily puzzle id={daily.id}")
        print("Demo users: demo0..demo11 (no auth required for guest viewing)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
