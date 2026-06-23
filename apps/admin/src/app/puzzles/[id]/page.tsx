import { notFound } from 'next/navigation';
import { AppShell } from '@/components/AppShell';
import { PlaytestForm } from '@/components/PlaytestForm';
import { ReviewActions } from '@/components/ReviewActions';
import { PuzzlePreviewGrid } from '@/components/PuzzlePreviewGrid';
import { apiFetch, ApiError } from '@/lib/api';
import styles from '@/lib/styles.module.css';
import type { AdminPuzzle } from '@/lib/types';

interface PuzzleDetailProps {
  readonly params: Promise<{ id: string }>;
}

export default async function PuzzleDetail({ params }: PuzzleDetailProps) {
  const { id } = await params;
  let puzzle: AdminPuzzle;
  try {
    puzzle = await apiFetch<AdminPuzzle>(`/admin/puzzles/${id}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  return (
    <AppShell title="Puzzle review">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 32 }}>
        <section>
          <h2 className={styles.sectionTitle}>Givens</h2>
          <PuzzlePreviewGrid grid={puzzle.givens} highlight="givens" />
          <h2 className={styles.sectionTitle} style={{ marginTop: 32 }}>Solution</h2>
          <PuzzlePreviewGrid grid={puzzle.solution} highlight="solution" />
        </section>
        <aside>
          <h2 className={styles.sectionTitle}>Metadata</h2>
          <dl style={{ fontSize: 13, lineHeight: 1.6 }}>
            <dt className={styles.muted}>ID</dt>
            <dd>
              <code className={styles.code}>{puzzle.id}</code>
            </dd>
            <dt className={styles.muted}>Difficulty</dt>
            <dd>{puzzle.difficulty}</dd>
            <dt className={styles.muted}>Status</dt>
            <dd>
              <span className={`${styles.badge} ${styles[puzzle.status]}`}>
                {puzzle.status.replace('_', ' ')}
              </span>
            </dd>
            <dt className={styles.muted}>Clues</dt>
            <dd>{puzzle.clue_count}</dd>
            <dt className={styles.muted}>Estimated solve</dt>
            <dd>
              {Math.round(puzzle.estimated_min_seconds / 60)}–{Math.round(puzzle.estimated_max_seconds / 60)} min
            </dd>
            <dt className={styles.muted}>Source</dt>
            <dd>{puzzle.source ?? '—'}</dd>
            <dt className={styles.muted}>License</dt>
            <dd>{puzzle.license ?? '—'}</dd>
            <dt className={styles.muted}>Notes</dt>
            <dd>{puzzle.notes ?? '—'}</dd>
            {puzzle.reviewed_at ? (
              <>
                <dt className={styles.muted}>Reviewed at</dt>
                <dd>{new Date(puzzle.reviewed_at).toLocaleString()}</dd>
              </>
            ) : null}
          </dl>
          <h2 className={styles.sectionTitle} style={{ marginTop: 24 }}>Actions</h2>
          <ReviewActions puzzleId={puzzle.id} status={puzzle.status} />
          <h2 className={styles.sectionTitle} style={{ marginTop: 24 }}>Playtest</h2>
          <p className={styles.muted} style={{ marginBottom: 8 }}>
            Record a manual solve. Saved to the admin audit log so reviewers can
            see how long the puzzle actually takes.
          </p>
          <PlaytestForm puzzleId={puzzle.id} />
        </aside>
      </div>
    </AppShell>
  );
}
