'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import styles from '@/lib/styles.module.css';
import type { PuzzleDifficulty } from '@/lib/types';

const DIFFICULTIES: readonly PuzzleDifficulty[] = ['easy', 'medium', 'hard', 'expert'];

interface FormState {
  readonly givens: string;
  readonly solution: string;
  readonly difficulty: PuzzleDifficulty;
  readonly estimatedMinMinutes: number;
  readonly estimatedMaxMinutes: number;
  readonly source: string;
  readonly license: string;
  readonly notes: string;
}

const DEFAULT_STATE: FormState = {
  givens: '',
  solution: '',
  difficulty: 'medium',
  estimatedMinMinutes: 5,
  estimatedMaxMinutes: 12,
  source: '',
  license: '',
  notes: '',
};

export function ImportForm() {
  const router = useRouter();
  const [state, setState] = useState<FormState>(DEFAULT_STATE);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [issues, setIssues] = useState<readonly string[] | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setState((prev) => ({ ...prev, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setPending(true);
    setError(null);
    setIssues(null);
    setSuccess(null);
    const givens = state.givens.replace(/\s+/g, '');
    const solution = state.solution.replace(/\s+/g, '');
    if (givens.length !== 81) {
      setError('Givens must be exactly 81 characters (0 or . for empty cells)');
      setPending(false);
      return;
    }
    try {
      const res = await fetch('/api/admin/puzzles/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          givens,
          solution: solution.length === 81 ? solution : undefined,
          difficulty: state.difficulty,
          estimated_min_seconds: Math.round(state.estimatedMinMinutes * 60),
          estimated_max_seconds: Math.round(state.estimatedMaxMinutes * 60),
          source: state.source || null,
          license: state.license || null,
          notes: state.notes || null,
        }),
      });
      const body = (await res.json().catch(() => ({}))) as {
        detail?: string;
        issues?: string[];
        id?: string;
      } | Array<{ id: string }>;
      if (!res.ok) {
        if (Array.isArray(body)) {
          setError('Validation failed');
        } else {
          setError(body.detail ?? 'Import failed');
          if (body.issues) setIssues(body.issues);
        }
        return;
      }
      const created = Array.isArray(body) ? body[0] : body;
      setSuccess('Puzzle imported and queued for review.');
      setState(DEFAULT_STATE);
      router.refresh();
      if (created?.id) {
        router.push(`/puzzles/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setPending(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      <label className={styles.label}>
        Givens (81 chars; 0/. for empty)
        <textarea
          className={styles.textarea}
          value={state.givens}
          onChange={(e) => update('givens', e.target.value)}
          placeholder="530070000600195000098000060800060003400803001700020006060000280000419005000080079"
          required
        />
      </label>
      <label className={styles.label}>
        Solution (optional — backend will compute the unique solution if omitted)
        <textarea
          className={styles.textarea}
          value={state.solution}
          onChange={(e) => update('solution', e.target.value)}
          placeholder="534678912672195348198342567859761423426853791713924856961537284287419635345286179"
        />
      </label>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
        <label className={styles.label}>
          Difficulty
          <select
            className={styles.select}
            value={state.difficulty}
            onChange={(e) => update('difficulty', e.target.value as PuzzleDifficulty)}
          >
            {DIFFICULTIES.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.label}>
          Estimate min (minutes)
          <input
            className={styles.input}
            type="number"
            min={1}
            max={120}
            value={state.estimatedMinMinutes}
            onChange={(e) => update('estimatedMinMinutes', Number(e.target.value))}
          />
        </label>
        <label className={styles.label}>
          Estimate max (minutes)
          <input
            className={styles.input}
            type="number"
            min={1}
            max={240}
            value={state.estimatedMaxMinutes}
            onChange={(e) => update('estimatedMaxMinutes', Number(e.target.value))}
          />
        </label>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <label className={styles.label}>
          Source
          <input
            className={styles.input}
            value={state.source}
            onChange={(e) => update('source', e.target.value)}
            placeholder="e.g. Public Domain CC0"
          />
        </label>
        <label className={styles.label}>
          License
          <input
            className={styles.input}
            value={state.license}
            onChange={(e) => update('license', e.target.value)}
            placeholder="e.g. CC0"
          />
        </label>
      </div>
      <label className={styles.label}>
        Notes
        <textarea
          className={styles.textarea}
          style={{ minHeight: 80 }}
          value={state.notes}
          onChange={(e) => update('notes', e.target.value)}
        />
      </label>
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
      <div>
        <button type="submit" className={styles.button} disabled={pending}>
          {pending ? 'Importing…' : 'Import puzzle'}
        </button>
      </div>
    </form>
  );
}
