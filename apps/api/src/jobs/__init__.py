"""Background jobs runnable from CLI or a scheduler.

The worker is intentionally simple — a single `run_due_jobs` entry point
that activates, finalizes, and times out work since the last invocation.
A cron/cron-job runner only needs to call `python -m src.jobs.worker tick`
to keep the system in sync.
"""

from src.jobs.tick import run_due_jobs

__all__ = ["run_due_jobs"]
