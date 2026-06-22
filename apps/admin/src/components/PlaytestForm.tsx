'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import styles from '@/lib/styles.module.css';

interface PlaytestFormProps {
  readonly puzzleId: string;
}

interface FormState {
  readonly minutes: number;
  readonly seconds: number;
  readonly mistakes: number;
  readonly notes: string;
}

const DEFAULT_STATE: FormState = {
  minutes: 4,
  seconds: 30,
  mistakes: 0,
  notes: '',
};

export function PlaytestForm({ puzzleId }: PlaytestFormProps) {
  const router = useRouter();
  const [state, setState] = useState<FormState>(DEFAULT_STATE);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setState((prev) => ({ ...prev, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setPending(true);
    setError(null);
    setSuccess(null);
    const duration_ms = Math.max(
      0,
      Math.round(state.minutes * 60_000 + state.seconds * 1_000),
    );
    if (duration_ms === 0) {
      setError('Duration must be greater than zero.');
      setPending(false);
      return;
    }
    try {
      const res = await fetch(`/api/admin/puzzles/${puzzleId}/playtest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          duration_ms,
          mistakes: state.mistakes,
          notes: state.notes || null,
        }),
      });
      if (!res.ok && res.status !== 204) {
        const body = (await res.json().catch(() => ({}))) as { detail?: string };
        setError(body.detail ?? `Playtest failed (${res.status})`);
        return;
      }
      setSuccess(
        `Playtest recorded: ${state.minutes}m ${state.seconds}s, ${state.mistakes} mistake(s).`,
      );
      setState({ ...DEFAULT_STATE });
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Network error');
    } finally {
      setPending(false);
    }
  }

  return (
    <form className={styles.form} onSubmit={submit} style={{ maxWidth: 'none' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
        <label className={styles.label}>
          Minutes
          <input
            className={styles.input}
            type="number"
            min={0}
            max={120}
            value={state.minutes}
            onChange={(e) => update('minutes', Math.max(0, Number(e.target.value)))}
          />
        </label>
        <label className={styles.label}>
          Seconds
          <input
            className={styles.input}
            type="number"
            min={0}
            max={59}
            value={state.seconds}
            onChange={(e) =>
              update('seconds', Math.max(0, Math.min(59, Number(e.target.value))))
            }
          />
        </label>
        <label className={styles.label}>
          Mistakes
          <input
            className={styles.input}
            type="number"
            min={0}
            max={99}
            value={state.mistakes}
            onChange={(e) => update('mistakes', Math.max(0, Number(e.target.value)))}
          />
        </label>
      </div>
      <label className={styles.label}>
        Playtest notes (optional)
        <textarea
          className={styles.textarea}
          style={{ minHeight: 70 }}
          value={state.notes}
          onChange={(e) => update('notes', e.target.value)}
          placeholder="Felt fair, no guessing required."
        />
      </label>
      {error ? <p className={styles.error}>{error}</p> : null}
      {success ? <p className={styles.success}>{success}</p> : null}
      <div>
        <button
          type="submit"
          className={`${styles.button} ${styles.buttonSecondary}`}
          disabled={pending}
        >
          {pending ? 'Recording…' : 'Record playtest'}
        </button>
      </div>
    </form>
  );
}
