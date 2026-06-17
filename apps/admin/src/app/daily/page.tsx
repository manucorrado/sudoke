import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { apiFetch, ApiError } from '@/lib/api';
import styles from '@/lib/styles.module.css';
import type { AdminDailyPuzzle } from '@/lib/types';

function fmtDate(value: string): string {
  return new Date(value).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
    timeZoneName: 'short',
  });
}

export default async function DailySchedule() {
  let dailies: readonly AdminDailyPuzzle[] = [];
  let error: string | null = null;
  try {
    dailies = await apiFetch<readonly AdminDailyPuzzle[]>('/admin/daily-puzzles?limit=200');
  } catch (err) {
    error = err instanceof ApiError ? `${err.status}: ${err.message}` : 'API request failed';
  }

  return (
    <AppShell title="Daily schedule">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <p className={styles.muted}>
          Approved puzzles scheduled for the daily ranked rotation.{' '}
          <Link href="/daily/schedule" className={styles.headerLink}>
            + Bulk schedule
          </Link>
        </p>
      </div>
      {error ? <p className={styles.error}>{error}</p> : null}
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Date (UTC)</th>
            <th>Difficulty</th>
            <th>Status</th>
            <th>Activates</th>
            <th>Finalizes</th>
            <th>Puzzle</th>
          </tr>
        </thead>
        <tbody>
          {dailies.length === 0 ? (
            <tr>
              <td colSpan={6} className={styles.muted} style={{ padding: 24, textAlign: 'center' }}>
                Nothing scheduled.
              </td>
            </tr>
          ) : (
            dailies.map((d) => (
              <tr key={d.id}>
                <td>{d.scheduled_for}</td>
                <td>{d.difficulty ?? '—'}</td>
                <td>
                  <span className={`${styles.badge} ${styles[d.status]}`}>{d.status}</span>
                </td>
                <td>{fmtDate(d.activate_at)}</td>
                <td>{fmtDate(d.finalize_at)}</td>
                <td>
                  <Link href={`/puzzles/${d.puzzle_id}`} className={styles.headerLink}>
                    <code className={styles.code}>{d.puzzle_id.slice(0, 8)}…</code>
                  </Link>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </AppShell>
  );
}
