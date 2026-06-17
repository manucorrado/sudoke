import { AppShell } from '@/components/AppShell';
import { ImportForm } from '@/components/ImportForm';

export default function ImportPage() {
  return (
    <AppShell title="Import puzzles">
      <p style={{ marginBottom: 24, color: '#6c6c80', fontSize: 14, maxWidth: 640 }}>
        Paste an 81-character puzzle grid (0 or . for empty cells) plus optional solution and metadata.
        The backend will validate uniqueness, solvability, and clue count before
        creating a record in <code>needs_review</code> state.
      </p>
      <ImportForm />
    </AppShell>
  );
}
