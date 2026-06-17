'use client';

import { useRouter } from 'next/navigation';
import { useMemo, useState } from 'react';
import styles from '@/lib/styles.module.css';
import type { AdminPuzzle } from '@/lib/types';

interface ScheduleFormProps {
  readonly approved: readonly AdminPuzzle[];
}

interface Row {
  readonly key: string;
  readonly puzzleId: string;
  readonly date: string;
}

function todayISO(): string {
  const now = new Date();
  return `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, '0')}-${String(now.getUTCDate()).padStart(2, '0')}`;
}

export function ScheduleForm({ approved }: ScheduleFormProps) {
  const router = useRouter();
  const [rows, setRows] = useState<readonly Row[]>([
    { key: '1', puzzleId: approved[0]?.id ?? '', date: todayISO() },
  ]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [issues, setIssues] = useState<readonly string[] | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const optionsByDifficulty = useMemo(() => {
    return approved.reduce<Record<string, AdminPuzzle[]>>((acc, p) => {
      (acc[p.difficulty] ??= []).push(p);
      return acc;
    }, {});
  }, [approved]);

  function addRow() {
    setRows((r) => [...r, { key: String(r.length + 1 + Math.random()), puzzleId: approved[0]?.id ?? '', date: todayISO() }]);
  }

  function removeRow(key: string) {
    setRows((r) => r.filter((row) => row.key !== key));
  }

  function updateRow(key: string, patch: Partial<Row>) {
    setRows((r) => r.map((row) => (row.key === key ? { ...row, ...patch } : row)));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setPending(true);
    setError(null);
    setIssues(null);
    setSuccess(null);
    const entries = rows
      .filter((r) => r.puzzleId && r.date)
      .map((r) => ({ puzzle_id: r.puzzleId, scheduled_for: r.date }));
    if (entries.length === 0) {
      setError('Add at least one row');
      setPending(false);
      return;
    }
    try {
      const res = await fetch('/api/admin/daily-puzzles/bulk-schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ entries }),
      });
      const body = (await res.json().catch(() => ({}))) as {
        detail?: string;
        issues?: string[];
      };
      if (!res.ok) {
        setError(body.detail ?? 'Scheduling failed');
        if (body.issues) setIssues(body.issues);
        return;
      }
      setSuccess(`Scheduled ${entries.length} puzzle(s).`);
      router.push('/daily');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setPending(false);
    }
  }

  if (approved.length === 0) {
    return (
      <p className={styles.muted}>
        No approved puzzles available. Approve puzzles from the Puzzles tab first.
      </p>
    );
  }

  return (
    <form onSubmit={submit} style={{ display: 'grid', gap: 16, maxWidth: 720 }}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Date (UTC)</th>
            <th>Puzzle</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <td>
                <input
                  type="date"
                  className={styles.input}
                  value={row.date}
                  onChange={(e) => updateRow(row.key, { date: e.target.value })}
                  required
                />
              </td>
              <td>
                <select
                  className={styles.select}
                  value={row.puzzleId}
                  onChange={(e) => updateRow(row.key, { puzzleId: e.target.value })}
                  required
                >
                  {Object.entries(optionsByDifficulty).map(([difficulty, puzzles]) => (
                    <optgroup key={difficulty} label={difficulty}>
                      {puzzles.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.id.slice(0, 8)} · {p.clue_count} clues · {p.source ?? 'unknown'}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </td>
              <td>
                <button
                  type="button"
                  className={`${styles.button} ${styles.buttonSecondary}`}
                  onClick={() => removeRow(row.key)}
                  disabled={rows.length === 1}
                >
                  Remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ display: 'flex', gap: 12 }}>
        <button type="button" className={`${styles.button} ${styles.buttonSecondary}`} onClick={addRow}>
          + Add row
        </button>
        <button type="submit" className={styles.button} disabled={pending}>
          {pending ? 'Scheduling…' : 'Schedule puzzles'}
        </button>
      </div>
      {error ? (
        <div className={styles.error}>
          <strong>{error}</strong>
          {issues ? (
            <ul style={{ margin: '8px 0 0 16px' }}>
              {issues.map((issue) => (
                <li key={issue}>{issue}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {success ? <p className={styles.success}>{success}</p> : null}
    </form>
  );
}
