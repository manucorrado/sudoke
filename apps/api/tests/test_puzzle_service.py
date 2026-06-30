from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from src.models import DailyPuzzle, Puzzle, PuzzleStatus, User
from src.models.puzzles import DailyPuzzleStatus, PuzzleDifficulty
from src.schemas.common import (
    BulkScheduleEntry,
    PuzzleAdminCreate,
)
from src.services.puzzles import (
    PuzzleImportError,
    approve_puzzle,
    get_active_daily_puzzle,
    import_puzzle,
    schedule_puzzles,
)
from src.sudoku.engine import parse_grid, serialize_grid, solve

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

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
SCREENSHOT_INVALID = (
    "530070000"
    "060019500"
    "000980000"
    "060800006"
    "000340008"
    "030017000"
    "020006060"
    "000028000"
    "004190005"
)


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
async def test_import_canonicalizes_dotted_givens(
    db_session: AsyncSession, admin_user: User
) -> None:
    payload = PuzzleAdminCreate(
        givens=EASY.replace("0", "."),
        difficulty="easy",
        estimated_min_seconds=180,
        estimated_max_seconds=360,
        source="manual",
        license="CC0",
    )
    puzzle = await import_puzzle(db_session, payload, actor=admin_user)
    await db_session.commit()
    assert puzzle.givens == EASY


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
async def test_import_rejects_invalid_givens_from_screenshot(
    db_session: AsyncSession, admin_user: User
) -> None:
    payload = PuzzleAdminCreate(
        givens=SCREENSHOT_INVALID,
        difficulty="easy",
        estimated_min_seconds=180,
        estimated_max_seconds=360,
        source="manual",
        license="CC0",
    )
    with pytest.raises(PuzzleImportError) as exc_info:
        await import_puzzle(db_session, payload, actor=admin_user)
    assert "given conflict" in " ".join(exc_info.value.issues).lower()


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
async def test_approve_revalidates_stored_puzzle(
    db_session: AsyncSession, admin_user: User
) -> None:
    puzzle = Puzzle(
        givens=SCREENSHOT_INVALID,
        solution=EASY_SOL,
        difficulty=PuzzleDifficulty.easy,
        status=PuzzleStatus.needs_review,
        estimated_min_seconds=180,
        estimated_max_seconds=360,
        clue_count=27,
        source="manual",
        license="CC0",
    )
    db_session.add(puzzle)
    await db_session.flush()

    with pytest.raises(PuzzleImportError) as exc_info:
        await approve_puzzle(db_session, puzzle, actor=admin_user, notes="ok")
    assert "stored validation" in " ".join(exc_info.value.issues)


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
async def test_schedule_revalidates_stored_puzzle(
    db_session: AsyncSession, admin_user: User
) -> None:
    puzzle = Puzzle(
        givens=SCREENSHOT_INVALID,
        solution=EASY_SOL,
        difficulty=PuzzleDifficulty.easy,
        status=PuzzleStatus.approved,
        estimated_min_seconds=180,
        estimated_max_seconds=360,
        clue_count=27,
        source="manual",
        license="CC0",
        reviewer_id=admin_user.id,
        reviewed_at=datetime.now(UTC),
    )
    db_session.add(puzzle)
    await db_session.flush()

    with pytest.raises(PuzzleImportError) as exc_info:
        await schedule_puzzles(
            db_session,
            [BulkScheduleEntry(puzzle_id=puzzle.id, scheduled_for=date(2026, 6, 19))],
            actor=admin_user,
        )
    assert "stored validation" in " ".join(exc_info.value.issues)


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


@pytest.mark.asyncio
async def test_current_daily_skips_invalid_stored_puzzle(
    db_session: AsyncSession, admin_user: User
) -> None:
    puzzle = Puzzle(
        givens=SCREENSHOT_INVALID,
        solution=EASY_SOL,
        difficulty=PuzzleDifficulty.easy,
        status=PuzzleStatus.approved,
        estimated_min_seconds=180,
        estimated_max_seconds=360,
        clue_count=27,
        source="manual",
        license="CC0",
        reviewer_id=admin_user.id,
        reviewed_at=datetime.now(UTC),
    )
    db_session.add(puzzle)
    await db_session.flush()

    now = datetime.now(UTC)
    db_session.add(
        DailyPuzzle(
            puzzle_id=puzzle.id,
            scheduled_for=date(2026, 6, 20),
            activate_at=now - timedelta(minutes=5),
            finalize_at=now + timedelta(hours=23),
            status=DailyPuzzleStatus.active,
        )
    )
    await db_session.flush()

    assert await get_active_daily_puzzle(db_session, now=now) is None
