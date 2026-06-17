import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { apiFetch, ApiError } from '@/lib/api';
import styles from '@/lib/styles.module.css';
import type { AdminDailyPuzzle, AdminPuzzle, PuzzleStatus } from '@/lib/types';

const STATUS_LABELS: Record<PuzzleStatus, string> = {
  imported: 'Imported',
  needs_review: 'Needs review',
  approved: 'Approved',
  rejected: 'Rejected',
  archived: 'Archived',
};

async function loadOverview() {
  try {
    const [puzzles, daily] = await Promise.all([
      apiFetch<readonly AdminPuzzle[]>('/admin/puzzles?limit=500'),
      apiFetch<readonly AdminDailyPuzzle[]>('/admin/daily-puzzles?limit=500'),
    ]);
    return { puzzles, daily, error: null as string | null };
  } catch (err) {
    const message =
      err instanceof ApiError
        ? `${err.status}: ${err.message}`
        : 'Failed to reach API. Is the FastAPI server running?';
    return { puzzles: [], daily: [], error: message };
  }
}

export default async function AdminDashboard() {
  const { puzzles, daily, error } = await loadOverview();

  const counts = puzzles.reduce<Record<PuzzleStatus, number>>(
    (acc, p) => {
      acc[p.status] = (acc[p.status] ?? 0) + 1;
      return acc;
    },
    { imported: 0, needs_review: 0, approved: 0, rejected: 0, archived: 0 },
  );

  const scheduled = daily.filter((d) => d.status !== 'cancelled');
  const upcoming = scheduled.filter((d) => new Date(d.activate_at) >= new Date()).length;
  const activeNow = scheduled.filter(
    (d) =>
      new Date(d.activate_at) <= new Date() &&
      new Date(d.finalize_at) > new Date(),
  ).length;

  return (
    <AppShell title="Sudoke Admin">
      {error ? <p className={styles.error}>{error}</p> : null}

      <h2 className={styles.sectionTitle}>Inventory</h2>
      <div className={styles.cardGrid}>
        {(Object.entries(STATUS_LABELS) as [PuzzleStatus, string][]).map(([status, label]) => (
          <div key={status} className={styles.card}>
            <div className={styles.cardLabel}>{label}</div>
            <div className={styles.cardValue}>{counts[status] ?? 0}</div>
          </div>
        ))}
      </div>

      <h2 className={styles.sectionTitle} style={{ marginTop: 40 }}>Daily schedule</h2>
      <div className={styles.cardGrid}>
        <div className={styles.card}>
          <div className={styles.cardLabel}>Scheduled total</div>
          <div className={styles.cardValue}>{scheduled.length}</div>
        </div>
        <div className={styles.card}>
          <div className={styles.cardLabel}>Active right now</div>
          <div className={styles.cardValue}>{activeNow}</div>
        </div>
        <div className={styles.card}>
          <div className={styles.cardLabel}>Upcoming</div>
          <div className={styles.cardValue}>{upcoming}</div>
        </div>
        <div className={styles.card}>
          <div className={styles.cardLabel}>Approved inventory</div>
          <div className={styles.cardValue}>
            {counts.approved} / 90 <span className={styles.muted}>(launch goal)</span>
          </div>
        </div>
      </div>

      <p className={styles.muted} style={{ marginTop: 32 }}>
        <Link href="/puzzles/import" className={styles.headerLink}>
          Import a puzzle
        </Link>{' '}
        ·{' '}
        <Link href="/puzzles?status=needs_review" className={styles.headerLink}>
          Review pending puzzles
        </Link>{' '}
        ·{' '}
        <Link href="/daily" className={styles.headerLink}>
          View daily calendar
        </Link>
      </p>
    </AppShell>
  );
}
