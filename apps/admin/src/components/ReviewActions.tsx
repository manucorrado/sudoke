'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import styles from '@/lib/styles.module.css';
import type { PuzzleStatus } from '@/lib/types';

interface ReviewActionsProps {
  readonly puzzleId: string;
  readonly status: PuzzleStatus;
}

type Action = 'approve' | 'reject' | 'playtest' | null;

export function ReviewActions({ puzzleId, status }: ReviewActionsProps) {
  const router = useRouter();
  const [pending, setPending] = useState<Action>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState('');

  async function call(action: Exclude<Action, null>) {
    setPending(action);
    setError(null);
    try {
      const path = `/api/admin/puzzles/${puzzleId}/${action}`;
      const res = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_notes: note || null }),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { detail?: string; issues?: string[] };
        setError(body.detail ?? `Request failed (${res.status})`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setPending(null);
    }
  }

  const canReview =
    status === 'needs_review' || status === 'imported' || status === 'rejected';

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <label className={styles.label}>
        Review note (optional)
        <textarea
          className={styles.textarea}
          style={{ minHeight: 80 }}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Reason or feedback for the puzzle author"
        />
      </label>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button
          type="button"
          className={styles.button}
          disabled={!canReview || pending !== null}
          onClick={() => call('approve')}
        >
          {pending === 'approve' ? 'Approving…' : 'Approve'}
        </button>
        <button
          type="button"
          className={`${styles.button} ${styles.buttonDanger}`}
          disabled={!canReview || pending !== null}
          onClick={() => call('reject')}
        >
          {pending === 'reject' ? 'Rejecting…' : 'Reject'}
        </button>
      </div>
      {error ? <p className={styles.error}>{error}</p> : null}
      {!canReview ? (
        <p className={styles.muted}>Puzzle is in {status.replace('_', ' ')} state.</p>
      ) : null}
    </div>
  );
}
