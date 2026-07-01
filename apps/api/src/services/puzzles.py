"""Puzzle ingestion, validation, review and scheduling logic."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src import sudoku
from src.models import DailyPuzzle, DailyPuzzleStatus, Puzzle, PuzzleStatus, User
from src.models.puzzles import PuzzleDifficulty
from src.services.audit import record_audit

if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterable

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.schemas.common import (
        BulkScheduleEntry,
        PlaytestRequest,
        PuzzleAdminCreate,
    )


class PuzzleImportError(Exception):
    """Raised when a puzzle fails validation or has duplicates."""

    def __init__(self, issues: list[str]) -> None:
        super().__init__("Puzzle import failed")
        self.issues = issues


async def find_duplicate_puzzle(session: AsyncSession, givens: str) -> Puzzle | None:
    result = await session.execute(select(Puzzle).where(Puzzle.givens == givens))
    return result.scalar_one_or_none()


def validate_stored_puzzle(puzzle: Puzzle) -> list[str]:
    """Validate a persisted puzzle before it can reach ranked play."""

    issues: list[str] = []
    try:
        givens_list = sudoku.parse_grid(puzzle.givens)
    except sudoku.SudokuError as exc:
        return [f"Stored givens are malformed: {exc}"]

    try:
        solution_list = sudoku.parse_grid(puzzle.solution)
    except sudoku.SudokuError as exc:
        return [f"Stored solution is malformed: {exc}"]

    result = sudoku.validate_puzzle(givens_list, solution=solution_list)
    if not result.ok or result.solution is None:
        return list(result.issues)

    canonical_givens = sudoku.serialize_grid(givens_list)
    canonical_solution = sudoku.serialize_grid(list(result.solution))
    if puzzle.givens != canonical_givens:
        issues.append("Stored givens are not canonical 0-filled grid digits")
    if puzzle.solution != canonical_solution:
        issues.append("Stored solution does not match canonical computed solution")
    if puzzle.clue_count != result.clue_count:
        issues.append(
            f"Stored clue_count is {puzzle.clue_count}; expected {result.clue_count}"
        )
    if puzzle.estimated_min_seconds > puzzle.estimated_max_seconds:
        issues.append("estimated_min_seconds must be <= estimated_max_seconds")
    return issues


def _raise_if_stored_puzzle_invalid(puzzle: Puzzle) -> None:
    issues = validate_stored_puzzle(puzzle)
    if issues:
        raise PuzzleImportError(
            [
                f"Puzzle {puzzle.id} failed stored validation: {issue}"
                for issue in issues
            ]
        )


async def import_puzzle(
    session: AsyncSession,
    payload: PuzzleAdminCreate,
    *,
    actor: User | None = None,
) -> Puzzle:
    """Import a puzzle, validating shape, uniqueness, and solvability."""

    givens_list = sudoku.parse_grid(payload.givens)
    solution_list = sudoku.parse_grid(payload.solution) if payload.solution else None
    canonical_givens = sudoku.serialize_grid(givens_list)

    result = sudoku.validate_puzzle(givens_list, solution=solution_list)
    if not result.ok or result.solution is None:
        raise PuzzleImportError(list(result.issues))

    if payload.estimated_min_seconds > payload.estimated_max_seconds:
        raise PuzzleImportError(
            ["estimated_min_seconds must be <= estimated_max_seconds"]
        )

    duplicate = await find_duplicate_puzzle(session, canonical_givens)
    if duplicate is not None:
        raise PuzzleImportError([f"Duplicate puzzle (existing id: {duplicate.id})"])

    puzzle = Puzzle(
        givens=canonical_givens,
        solution=sudoku.serialize_grid(list(result.solution)),
        difficulty=PuzzleDifficulty(payload.difficulty),
        status=PuzzleStatus.needs_review,
        estimated_min_seconds=payload.estimated_min_seconds,
        estimated_max_seconds=payload.estimated_max_seconds,
        clue_count=result.clue_count,
        source=payload.source,
        license=payload.license,
        notes=payload.notes,
    )
    session.add(puzzle)
    await session.flush()
    await record_audit(
        session,
        actor=actor,
        action="puzzle.imported",
        target_type="puzzle",
        target_id=str(puzzle.id),
        payload={"difficulty": payload.difficulty},
    )
    return puzzle


async def approve_puzzle(
    session: AsyncSession, puzzle: Puzzle, *, actor: User, notes: str | None = None
) -> Puzzle:
    if puzzle.status not in (PuzzleStatus.needs_review, PuzzleStatus.imported):
        raise PuzzleImportError(
            [f"Cannot approve puzzle in status {puzzle.status.value}"]
        )
    _raise_if_stored_puzzle_invalid(puzzle)
    if puzzle.source is None or puzzle.license is None:
        raise PuzzleImportError(["Approved puzzles must have source and license set"])
    puzzle.status = PuzzleStatus.approved
    puzzle.reviewer_id = actor.id
    puzzle.reviewed_at = datetime.now(UTC)
    puzzle.review_notes = notes
    await record_audit(
        session,
        actor=actor,
        action="puzzle.approved",
        target_type="puzzle",
        target_id=str(puzzle.id),
        payload={"notes": notes},
    )
    return puzzle


async def reject_puzzle(
    session: AsyncSession, puzzle: Puzzle, *, actor: User, notes: str | None = None
) -> Puzzle:
    puzzle.status = PuzzleStatus.rejected
    puzzle.reviewer_id = actor.id
    puzzle.reviewed_at = datetime.now(UTC)
    puzzle.review_notes = notes
    await record_audit(
        session,
        actor=actor,
        action="puzzle.rejected",
        target_type="puzzle",
        target_id=str(puzzle.id),
        payload={"notes": notes},
    )
    return puzzle


async def record_playtest(
    session: AsyncSession,
    puzzle: Puzzle,
    *,
    actor: User,
    payload: PlaytestRequest,
) -> None:
    """Records a playtest result in the audit log.

    A dedicated `puzzle_playtests` table is a post-MVP nicety — this audit
    entry is enough for the review workflow.
    """

    await record_audit(
        session,
        actor=actor,
        action="puzzle.playtested",
        target_type="puzzle",
        target_id=str(puzzle.id),
        payload={
            "duration_ms": payload.duration_ms,
            "mistakes": payload.mistakes,
            "notes": payload.notes,
        },
    )


def _activation_window(scheduled_for: date) -> tuple[datetime, datetime]:
    """Return UTC (activate_at, finalize_at) for the given puzzle date.

    The MVP uses a fixed global window: 00:00 UTC -> 00:00 UTC next day.
    Configurable in §10.2.
    """

    activate_at = datetime.combine(scheduled_for, time.min, tzinfo=UTC)
    finalize_at = activate_at + timedelta(days=1)
    return activate_at, finalize_at


async def schedule_puzzles(
    session: AsyncSession,
    entries: Iterable[BulkScheduleEntry],
    *,
    actor: User,
) -> list[tuple[DailyPuzzle, Puzzle]]:
    """Bulk schedule approved puzzles. Returns (daily, puzzle) pairs."""

    scheduled: list[tuple[DailyPuzzle, Puzzle]] = []
    for entry in entries:
        puzzle = await session.get(Puzzle, entry.puzzle_id)
        if puzzle is None:
            raise PuzzleImportError([f"Puzzle {entry.puzzle_id} not found"])
        if puzzle.status != PuzzleStatus.approved:
            raise PuzzleImportError(
                [f"Puzzle {puzzle.id} is not approved (status={puzzle.status.value})"]
            )
        _raise_if_stored_puzzle_invalid(puzzle)
        if puzzle.difficulty == PuzzleDifficulty.expert:
            raise PuzzleImportError(
                ["Expert puzzles are excluded from the MVP ranked rotation"]
            )
        activate_at, finalize_at = _activation_window(entry.scheduled_for)
        daily = DailyPuzzle(
            puzzle_id=puzzle.id,
            scheduled_for=entry.scheduled_for,
            activate_at=activate_at,
            finalize_at=finalize_at,
            status=DailyPuzzleStatus.scheduled,
        )
        session.add(daily)
        scheduled.append((daily, puzzle))
    try:
        await session.flush()
    except IntegrityError as exc:
        raise PuzzleImportError([
            "One or more dates already have a scheduled puzzle",
        ]) from exc
    await record_audit(
        session,
        actor=actor,
        action="daily.scheduled",
        target_type="daily_puzzles",
        target_id=None,
        payload={"count": len(scheduled)},
    )
    return scheduled


async def get_active_daily_puzzle(
    session: AsyncSession, *, now: datetime | None = None
) -> DailyPuzzle | None:
    """Returns the currently active puzzle, or None if none scheduled."""

    moment = now or datetime.now(UTC)
    result = await session.execute(
        select(DailyPuzzle)
        .where(DailyPuzzle.activate_at <= moment)
        .where(DailyPuzzle.finalize_at > moment)
        .where(
            DailyPuzzle.status.in_(
                (DailyPuzzleStatus.scheduled, DailyPuzzleStatus.active)
            )
        )
        .order_by(DailyPuzzle.scheduled_for.desc())
        .limit(1)
    )
    daily = result.scalar_one_or_none()
    if daily is None or daily.puzzle is None:
        return None
    if validate_stored_puzzle(daily.puzzle):
        return None
    return daily


async def activate_due_daily_puzzles(
    session: AsyncSession, *, now: datetime | None = None
) -> list[uuid.UUID]:
    """Mark scheduled puzzles whose activation window opens as active."""

    moment = now or datetime.now(UTC)
    result = await session.execute(
        select(DailyPuzzle)
        .where(DailyPuzzle.status == DailyPuzzleStatus.scheduled)
        .where(DailyPuzzle.activate_at <= moment)
    )
    activated: list[uuid.UUID] = []
    for daily in result.scalars():
        daily.status = DailyPuzzleStatus.active
        activated.append(daily.id)
    return activated


async def finalize_due_daily_puzzles(
    session: AsyncSession, *, now: datetime | None = None
) -> list[uuid.UUID]:
    """Move puzzles past their finalize_at window into the finalized state."""

    moment = now or datetime.now(UTC)
    result = await session.execute(
        select(DailyPuzzle)
        .where(
            DailyPuzzle.status.in_(
                (DailyPuzzleStatus.scheduled, DailyPuzzleStatus.active)
            )
        )
        .where(DailyPuzzle.finalize_at <= moment)
    )
    finalized: list[uuid.UUID] = []
    for daily in result.scalars():
        daily.status = DailyPuzzleStatus.finalized
        finalized.append(daily.id)
    return finalized
