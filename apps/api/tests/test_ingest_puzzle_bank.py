"""Unit tests for the puzzle-bank ingestion script."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scripts import ingest_puzzle_bank as ingest
from src.models import DailyPuzzle, Puzzle, PuzzleStatus

# Five real lines from data/raw/sudoku_exchange/easy.txt (all unique-solution,
# 1.2 difficulty). Kept inline so tests don't depend on the data dir.
# Lines exceed ruff's E501 width; the existing API codebase does not enforce
# ruff so we accept the long-line readability tradeoff here.
SAMPLE_LINES = [  # noqa: E501
    "0000183b305c 050703060007000800000816000000030000005000100730040086906000204840572093000409000  1.2",  # noqa: E501
    "0001d5d6314e 302401809001000300000000000040708010780502036000090000200609003900000008800070005  1.2",  # noqa: E501
    "000212406270 000823001003000400070000052300960010000102000010038006830000040002000900600789000  1.2",  # noqa: E501
    "00023580f347 500700032100326000000000000020070058010803040890040070000000000000654001230009005  1.2",  # noqa: E501
    "00031006ebf1 760000053020080040005000900000000000040010070603000104100304009000000000006827300  1.2",  # noqa: E501
]


def test_parse_source_line_happy_path() -> None:
    line = SAMPLE_LINES[0]
    parsed = ingest.parse_source_line(line)
    assert parsed is not None
    src_hash, givens, rating = parsed
    assert src_hash == "0000183b305c"
    assert len(givens) == 81
    assert rating == pytest.approx(1.2)


def test_parse_source_line_skips_blank() -> None:
    assert ingest.parse_source_line("") is None
    assert ingest.parse_source_line("   \n") is None


def test_parse_source_line_rejects_bad_shape() -> None:
    with pytest.raises(ValueError):
        ingest.parse_source_line("only two columns")
    with pytest.raises(ValueError):
        ingest.parse_source_line("a TOO_SHORT 1.0")
    with pytest.raises(ValueError):
        ingest.parse_source_line(
            "a "
            + "x" * 81  # invalid characters
            + " 1.0"
        )


def test_parse_source_line_accepts_dots_as_blanks() -> None:
    dotted = SAMPLE_LINES[0].replace("0", ".")
    parsed = ingest.parse_source_line(dotted)
    assert parsed is not None
    _, givens, _ = parsed
    assert "." not in givens
    assert "0" in givens


def test_iter_source_file_respects_limit(tmp_path: Path) -> None:
    p = tmp_path / "bank.txt"
    p.write_text("\n".join(SAMPLE_LINES) + "\n")
    rows = list(ingest.iter_source_file(p, limit=3))
    assert len(rows) == 3
    assert rows[0].source_hash == "0000183b305c"
    assert rows[2].source_hash == "000212406270"


@pytest.mark.asyncio
async def test_import_and_approve_writes_approved_puzzles(
    db_session: AsyncSession,
) -> None:
    actor = await ingest.ensure_admin_user(db_session, auth_id="admin-test")
    await db_session.commit()

    rows = []
    for line in SAMPLE_LINES:
        parsed = ingest.parse_source_line(line)
        assert parsed is not None
        src_hash, givens, rating = parsed
        rows.append(
            ingest.RawPuzzleRow(
                source_hash=src_hash,
                givens=givens,
                source_rating=rating,
                source_file="easy.txt",
                source_line=1,
            )
        )

    stats = ingest.IngestStats()
    inserted = await ingest.import_and_approve(
        db_session, rows, difficulty="easy", actor=actor, stats=stats
    )
    await db_session.commit()

    assert len(inserted) == 5
    assert stats.inserted == 5
    assert stats.approved == 5
    assert stats.rejected_invalid == 0

    result = await db_session.execute(select(Puzzle))
    puzzles = list(result.scalars())
    assert len(puzzles) == 5
    for p in puzzles:
        assert p.status == PuzzleStatus.approved
        assert p.source == ingest.DEFAULT_SOURCE_NAME
        assert p.license == ingest.DEFAULT_SOURCE_LICENSE
        assert p.reviewer_id == actor.id


@pytest.mark.asyncio
async def test_import_and_approve_is_idempotent(
    db_session: AsyncSession,
) -> None:
    actor = await ingest.ensure_admin_user(db_session, auth_id="admin-test")
    await db_session.commit()

    rows = []
    for line in SAMPLE_LINES[:3]:
        parsed = ingest.parse_source_line(line)
        assert parsed is not None
        src_hash, givens, rating = parsed
        rows.append(
            ingest.RawPuzzleRow(
                source_hash=src_hash,
                givens=givens,
                source_rating=rating,
                source_file="easy.txt",
                source_line=1,
            )
        )

    stats1 = ingest.IngestStats()
    inserted1 = await ingest.import_and_approve(
        db_session, rows, difficulty="easy", actor=actor, stats=stats1
    )
    await db_session.commit()
    assert len(inserted1) == 3

    stats2 = ingest.IngestStats()
    inserted2 = await ingest.import_and_approve(
        db_session, rows, difficulty="easy", actor=actor, stats=stats2
    )
    await db_session.commit()
    assert inserted2 == []
    assert stats2.skipped_existing == 3
    assert stats2.inserted == 0


@pytest.mark.asyncio
async def test_schedule_puzzles_skips_taken_dates(
    db_session: AsyncSession,
) -> None:
    actor = await ingest.ensure_admin_user(db_session, auth_id="admin-test")
    await db_session.commit()

    rows = []
    for line in SAMPLE_LINES[:3]:
        parsed = ingest.parse_source_line(line)
        assert parsed is not None
        src_hash, givens, rating = parsed
        rows.append(
            ingest.RawPuzzleRow(
                source_hash=src_hash,
                givens=givens,
                source_rating=rating,
                source_file="easy.txt",
                source_line=1,
            )
        )

    stats = ingest.IngestStats()
    inserted = await ingest.import_and_approve(
        db_session, rows, difficulty="easy", actor=actor, stats=stats
    )
    await db_session.commit()

    start = date(2030, 1, 1)
    scheduled = await ingest.schedule_puzzles(
        db_session, inserted, start_date=start, actor=actor, stats=stats
    )
    await db_session.commit()
    assert [d.scheduled_for for d in scheduled] == [
        date(2030, 1, 1),
        date(2030, 1, 2),
        date(2030, 1, 3),
    ]

    # Re-schedule the remaining puzzles: every existing date is skipped
    # and nothing new is created since the inserted list is exhausted.
    stats2 = ingest.IngestStats()
    again = await ingest.schedule_puzzles(
        db_session, [], start_date=start, actor=actor, stats=stats2
    )
    await db_session.commit()
    assert again == []
    assert stats2.scheduled == 0

    rows_after = await db_session.execute(select(DailyPuzzle))
    assert len(list(rows_after.scalars())) == 3
