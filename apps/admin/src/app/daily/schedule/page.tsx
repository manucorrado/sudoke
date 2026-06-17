import { AppShell } from '@/components/AppShell';
import { ScheduleForm } from '@/components/ScheduleForm';
import { apiFetch, ApiError } from '@/lib/api';
import styles from '@/lib/styles.module.css';
import type { AdminPuzzle } from '@/lib/types';

export default async function SchedulePage() {
  let approved: readonly AdminPuzzle[] = [];
  let error: string | null = null;
  try {
    approved = await apiFetch<readonly AdminPuzzle[]>('/admin/puzzles?status=approved&limit=500');
  } catch (err) {
    error = err instanceof ApiError ? `${err.status}: ${err.message}` : 'API request failed';
  }

  return (
    <AppShell title="Bulk schedule">
      <p style={{ color: '#6c6c80', fontSize: 14, marginBottom: 24, maxWidth: 640 }}>
        Assign approved puzzles to specific UTC dates. The activation cron
        flips each row to <code>active</code> when its window opens.
      </p>
      {error ? <p className={styles.error}>{error}</p> : null}
      <ScheduleForm approved={approved} />
    </AppShell>
  );
}
