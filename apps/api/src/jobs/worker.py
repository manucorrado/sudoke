"""CLI entry point for the cron worker.

Usage:

    python -m src.jobs.worker tick     # one-shot
    python -m src.jobs.worker loop --interval 60   # forever-loop fallback
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone

import structlog

from src.db.session import async_session_factory, engine
from src.jobs.tick import run_due_jobs

logger = structlog.get_logger("worker")


async def _tick() -> None:
    async with async_session_factory() as session:
        try:
            report = await run_due_jobs(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
    logger.info(
        "worker.tick",
        activated=len(report.activated),
        timed_out=len(report.timed_out_attempts),
        finalized_dailies=len(report.finalized_dailies),
        rated_attempts=report.rated_attempts,
        ts=datetime.now(timezone.utc).isoformat(),
    )


async def _loop(interval_s: float) -> None:
    while True:
        try:
            await _tick()
        except Exception:
            logger.exception("worker.tick_failed")
        await asyncio.sleep(interval_s)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sudoke-worker")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tick", help="Run pending jobs once and exit")
    loop = sub.add_parser("loop", help="Run pending jobs in a forever loop")
    loop.add_argument("--interval", type=float, default=60.0)
    args = parser.parse_args(argv)

    try:
        if args.cmd == "tick":
            asyncio.run(_tick())
        elif args.cmd == "loop":
            asyncio.run(_loop(args.interval))
    finally:
        asyncio.run(engine.dispose())
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
