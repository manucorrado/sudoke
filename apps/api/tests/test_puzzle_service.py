from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import PuzzleStatus, User
from src.schemas.common import (
    BulkScheduleEntry,
    PuzzleAdminCreate,
)
from src.services.puzzles import (
    PuzzleImportError,
    approve_puzzle,
    import_puzzle,
    schedule_puzzles,
)
from src.sudoku.engine import solve, parse_grid, serialize_grid

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


@pytest.mark.asyncio
async def test_import_valid_puzzle(db_session: AsyncSession, admin_user: User) -> None:
    payload = PuzzleAdminCreate(
        givens=EASY,
        solution=EASY_SOL,
        difficulty="easy",
        estimated_min_seconds=180,
        estimated_max_seconds=360,
        source="manual",
        license="CC0",
    )
    puzzle = await import_puzzle(db_session, payload, actor=admin_user)
    await db_session.commit()
    assert puzzle.status == PuzzleStatus.needs_review
    assert puzzle.clue_count > 17
    assert puzzle.solution == EASY_SOL


@pytest.mark.asyncio
async def test_import_rejects_invalid_solution(
    db_session: AsyncSession, admin_user: User
) -> None:
    bad_solution = "1" * 81
    payload = PuzzleAdminCreate(
        givens=EASY,
        solution=bad_solution,
        difficulty="easy",
        estimated_min_seconds=180,
        estimated_max_seconds=360,
    )
    with pytest.raises(PuzzleImportError):
        await import_puzzle(db_session, payload, actor=admin_user)


@pytest.mark.asyncio
async def test_import_rejects_duplicate(
    db_session: AsyncSession, admin_user: User
) -> None:
    payload = PuzzleAdminCreate(
        givens=EASY,
        difficulty="easy",
        estimated_min_seconds=180,
        estimated_max_seconds=360,
        source="manual",
        license="CC0",
    )
    await import_puzzle(db_session, payload, actor=admin_user)
    await db_session.commit()
    with pytest.raises(PuzzleImportError):
        await import_puzzle(db_session, payload, actor=admin_user)


@pytest.mark.asyncio
async def test_approve_and_schedule(
    db_session: AsyncSession, admin_user: User
) -> None:
    payload = PuzzleAdminCreate(
        givens=EASY,
        difficulty="easy",
        estimated_min_seconds=180,
        estimated_max_seconds=360,
        source="manual",
        license="CC0",
    )
    puzzle = await import_puzzle(db_session, payload, actor=admin_user)
    await approve_puzzle(db_session, puzzle, actor=admin_user, notes="ok")
    scheduled = await schedule_puzzles(
        db_session,
        [BulkScheduleEntry(puzzle_id=puzzle.id, scheduled_for=date(2026, 6, 17))],
        actor=admin_user,
    )
    await db_session.commit()
    assert len(scheduled) == 1
    daily, scheduled_puzzle = scheduled[0]
    assert daily.puzzle_id == puzzle.id
    assert scheduled_puzzle.id == puzzle.id


@pytest.mark.asyncio
async def test_schedule_requires_approval(
    db_session: AsyncSession, admin_user: User
) -> None:
    payload = PuzzleAdminCreate(
        givens=EASY,
        difficulty="easy",
        estimated_min_seconds=180,
        estimated_max_seconds=360,
        source="manual",
        license="CC0",
    )
    puzzle = await import_puzzle(db_session, payload, actor=admin_user)
    await db_session.commit()
    with pytest.raises(PuzzleImportError):
        await schedule_puzzles(
            db_session,
            [BulkScheduleEntry(puzzle_id=puzzle.id, scheduled_for=date(2026, 6, 18))],
            actor=admin_user,
        )
