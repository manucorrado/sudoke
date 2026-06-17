import Link from 'next/link';
import { AppShell } from '@/components/AppShell';
import { apiFetch, ApiError } from '@/lib/api';
import styles from '@/lib/styles.module.css';
import type { AdminPuzzle, PuzzleStatus } from '@/lib/types';

const STATUS_OPTIONS: readonly (PuzzleStatus | 'all')[] = [
  'all',
  'imported',
  'needs_review',
  'approved',
  'rejected',
  'archived',
];

interface PuzzlesPageProps {
  readonly searchParams: Promise<{ status?: string }>;
}

export default async function PuzzlesPage({ searchParams }: PuzzlesPageProps) {
  const { status } = await searchParams;
  const filter = STATUS_OPTIONS.includes((status as PuzzleStatus | 'all') ?? 'all')
    ? (status as PuzzleStatus | 'all' | undefined)
    : 'all';

  let puzzles: readonly AdminPuzzle[] = [];
  let error: string | null = null;
  try {
    const query = filter && filter !== 'all' ? `?status=${filter}` : '';
    puzzles = await apiFetch<readonly AdminPuzzle[]>(`/admin/puzzles${query}`);
  } catch (err) {
    error = err instanceof ApiError ? `${err.status}: ${err.message}` : 'API request failed';
  }

  return (
    <AppShell title="Puzzles">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <nav style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {STATUS_OPTIONS.map((opt) => {
            const isActive = (filter ?? 'all') === opt;
            return (
              <Link
                key={opt}
                href={opt === 'all' ? '/puzzles' : `/puzzles?status=${opt}`}
                className={styles.headerLink}
                style={{
                  padding: '6px 12px',
                  borderRadius: 999,
                  background: isActive ? '#1a1a2e' : '#eef2ff',
                  color: isActive ? '#fff' : '#1a1a2e',
                  fontSize: 12,
                }}
              >
                {opt.replace('_', ' ')}
              </Link>
            );
          })}
        </nav>
        <Link href="/puzzles/import" className={styles.headerLink}>
          + Import puzzle
        </Link>
      </div>

      {error ? <p className={styles.error}>{error}</p> : null}

      <table className={styles.table}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Difficulty</th>
            <th>Status</th>
            <th>Clues</th>
            <th>Estimated</th>
            <th>License</th>
            <th>Reviewed</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {puzzles.length === 0 ? (
            <tr>
              <td colSpan={8} className={styles.muted} style={{ padding: 24, textAlign: 'center' }}>
                No puzzles found.
              </td>
            </tr>
          ) : (
            puzzles.map((p) => (
              <tr key={p.id}>
                <td>
                  <code className={styles.code}>{p.id.slice(0, 8)}…</code>
                </td>
                <td>{p.difficulty}</td>
                <td>
                  <span className={`${styles.badge} ${styles[p.status]}`}>{p.status.replace('_', ' ')}</span>
                </td>
                <td>{p.clue_count}</td>
                <td>
                  {Math.round(p.estimated_min_seconds / 60)}–{Math.round(p.estimated_max_seconds / 60)} min
                </td>
                <td>
                  {p.license ?? <span className={styles.muted}>—</span>}
                </td>
                <td>{p.reviewed_at ? new Date(p.reviewed_at).toLocaleDateString() : '—'}</td>
                <td>
                  <Link href={`/puzzles/${p.id}`} className={styles.headerLink}>
                    Review →
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
