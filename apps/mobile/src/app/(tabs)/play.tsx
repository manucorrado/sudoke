import { useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import {
  applyAutoFillNotes,
  createGame,
  FIXTURE_PUZZLES,
  makeCasualRules,
  type CasualOverrides,
  type CreateGameInput,
  type GameState,
  type Puzzle,
  type PuzzleDifficulty,
} from '@sudoke/sudoku-core';
import { GameScreen } from '@/features/game/GameScreen';
import { ArchiveReplayCard } from '@/features/archive/ArchiveReplayCard';
import {
  puzzleFromArchive,
  useArchiveDetail,
  useArchiveList,
  useUpcoming,
} from '@/features/archive/useArchive';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

const DIFFICULTY_OPTIONS: readonly PuzzleDifficulty[] = ['easy', 'medium', 'hard'];

const MISTAKE_OPTIONS: readonly { label: string; value: number | null }[] = [
  { label: '3', value: 3 },
  { label: '5', value: 5 },
  { label: '∞', value: null },
];

type TabKey = 'casual' | 'archive' | 'upcoming';

const TABS: readonly { key: TabKey; label: string }[] = [
  { key: 'casual', label: 'Casual' },
  { key: 'archive', label: 'Archive' },
  { key: 'upcoming', label: 'Upcoming' },
];

interface ActiveArchive {
  readonly dailyPuzzleId: string;
  readonly scheduledFor: string;
  readonly difficulty: PuzzleDifficulty;
}

export function PlayScreen() {
  const [tab, setTab] = useState<TabKey>('casual');
  const [difficulty, setDifficulty] = useState<PuzzleDifficulty>('easy');
  const [overrides, setOverrides] = useState<CasualOverrides>({
    maxMistakes: 3,
    hintsEnabled: false,
    autoFillNotes: false,
    autoClearNotes: true,
  });
  const [active, setActive] = useState<CreateGameInput | null>(null);
  const [activeArchive, setActiveArchive] = useState<ActiveArchive | null>(null);

  const puzzle = useMemo(
    () => FIXTURE_PUZZLES.find((p) => p.metadata.difficulty === difficulty) ?? FIXTURE_PUZZLES[0]!,
    [difficulty],
  );

  if (activeArchive) {
    return (
      <View style={styles.gameWrap}>
        <Pressable onPress={() => setActiveArchive(null)} style={styles.backButton}>
          <Text style={styles.backText}>← Back to Play</Text>
        </Pressable>
        <ArchiveReplayLoader entry={activeArchive} />
      </View>
    );
  }

  if (active) {
    return (
      <View style={styles.gameWrap}>
        <Pressable onPress={() => setActive(null)} style={styles.backButton}>
          <Text style={styles.backText}>← Back to Play</Text>
        </Pressable>
        <GameScreen initial={active} title={`Casual · ${difficulty}`} />
      </View>
    );
  }

  const handleStart = () => {
    const rules = makeCasualRules(overrides);
    let seedState: GameState | undefined;
    if (overrides.autoFillNotes) {
      seedState = applyAutoFillNotes(createGame({ puzzle, rules }));
    }
    const next: CreateGameInput = { puzzle, rules };
    setActive(seedState ? ({ ...next, seedState } as CreateGameInput & { seedState: GameState }) : next);
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Play</Text>
      <Text style={styles.subtitle}>
        Practice with custom settings, replay closed dailies, or peek at the upcoming calendar.
      </Text>

      <View style={styles.tabBar} accessibilityRole="tablist">
        {TABS.map((t) => {
          const isActive = t.key === tab;
          return (
            <Pressable
              key={t.key}
              onPress={() => setTab(t.key)}
              style={[styles.tab, isActive && styles.tabActive]}
              accessibilityRole="tab"
              accessibilityState={{ selected: isActive }}
            >
              <Text style={[styles.tabText, isActive && styles.tabTextActive]}>{t.label}</Text>
            </Pressable>
          );
        })}
      </View>

      {tab === 'casual' ? (
        <CasualSettings
          difficulty={difficulty}
          onDifficultyChange={setDifficulty}
          overrides={overrides}
          onOverridesChange={setOverrides}
          onStart={handleStart}
        />
      ) : tab === 'archive' ? (
        <ArchiveList onPlay={setActiveArchive} />
      ) : (
        <UpcomingList />
      )}
    </ScrollView>
  );
}

interface CasualSettingsProps {
  readonly difficulty: PuzzleDifficulty;
  readonly onDifficultyChange: (d: PuzzleDifficulty) => void;
  readonly overrides: CasualOverrides;
  readonly onOverridesChange: (update: (prev: CasualOverrides) => CasualOverrides) => void;
  readonly onStart: () => void;
}

function CasualSettings({
  difficulty,
  onDifficultyChange,
  overrides,
  onOverridesChange,
  onStart,
}: CasualSettingsProps) {
  return (
    <View style={{ gap: spacing.md }}>
      <Section title="Difficulty">
        <Segmented
          options={DIFFICULTY_OPTIONS.map((d) => ({ label: capitalize(d), value: d }))}
          value={difficulty}
          onChange={onDifficultyChange}
        />
      </Section>
      <Section title="Mistake limit">
        <Segmented
          options={MISTAKE_OPTIONS}
          value={overrides.maxMistakes ?? null}
          onChange={(v) => onOverridesChange((prev) => ({ ...prev, maxMistakes: v }))}
        />
      </Section>
      <Section title="Auto-clear notes">
        <Toggle
          value={overrides.autoClearNotes ?? true}
          onChange={(v) => onOverridesChange((prev) => ({ ...prev, autoClearNotes: v }))}
        />
      </Section>
      <Section title="Auto-fill notes (casual only)">
        <Toggle
          value={overrides.autoFillNotes ?? false}
          onChange={(v) => onOverridesChange((prev) => ({ ...prev, autoFillNotes: v }))}
        />
      </Section>
      <Section title="Hints (casual only)">
        <Toggle
          value={overrides.hintsEnabled ?? false}
          onChange={(v) => onOverridesChange((prev) => ({ ...prev, hintsEnabled: v }))}
        />
      </Section>
      <Pressable style={styles.startButton} onPress={onStart} accessibilityRole="button">
        <Text style={styles.startButtonText}>Start Game</Text>
      </Pressable>
    </View>
  );
}

interface ArchiveLoaderProps {
  readonly entry: ActiveArchive;
}

function ArchiveReplayLoader({ entry }: ArchiveLoaderProps) {
  const detail = useArchiveDetail(entry.dailyPuzzleId);
  const puzzle: Puzzle | null = useMemo(() => {
    if (!detail.data) return null;
    try {
      return puzzleFromArchive(detail.data);
    } catch {
      return null;
    }
  }, [detail.data]);
  if (detail.isLoading) return <Loading text="Loading puzzle…" />;
  if (detail.error || !puzzle) {
    return (
      <ErrorBlock
        message="Couldn't load this archive puzzle."
        onRetry={() => void detail.refetch()}
      />
    );
  }
  return (
    <ArchiveReplayCard
      dailyPuzzleId={entry.dailyPuzzleId}
      scheduledFor={entry.scheduledFor}
      difficulty={entry.difficulty}
      puzzle={puzzle}
      rules={makeCasualRules({
        maxMistakes: 3,
        hintsEnabled: false,
        autoFillNotes: false,
      })}
    />
  );
}

interface ArchiveListProps {
  readonly onPlay: (entry: ActiveArchive) => void;
}

function ArchiveList({ onPlay }: ArchiveListProps) {
  const { data, isLoading, error, refetch, isRefetching } = useArchiveList({ limit: 30 });
  if (isLoading) return <Loading text="Loading archive…" />;
  if (error) {
    return <ErrorBlock message="Couldn't load the archive." onRetry={() => void refetch()} />;
  }
  const entries = data?.entries ?? [];
  if (entries.length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyTitle}>Archive is empty</Text>
        <Text style={styles.emptyBody}>
          Closed daily puzzles will appear here for unlimited practice. None have finalized yet.
        </Text>
        <Text style={styles.note}>
          Archive plays are practice-only — they never affect your rating.
        </Text>
      </View>
    );
  }
  return (
    <View style={{ gap: spacing.sm }}>
      <Text style={styles.note}>
        Replay closed dailies. Casual rules apply — your rating and the historical leaderboard stay
        untouched.
      </Text>
      {entries.map((entry) => (
        <Pressable
          key={entry.daily_puzzle_id}
          style={styles.archiveRow}
          onPress={() =>
            onPlay({
              dailyPuzzleId: entry.daily_puzzle_id,
              scheduledFor: entry.scheduled_for,
              difficulty: entry.difficulty as PuzzleDifficulty,
            })
          }
          accessibilityRole="button"
        >
          <View style={{ flex: 1 }}>
            <Text style={styles.archiveDate}>{formatDate(entry.scheduled_for)}</Text>
            <Text style={styles.archiveMeta}>
              {capitalize(entry.difficulty)} · est{' '}
              {Math.round(entry.estimated_min_seconds / 60)}–
              {Math.round(entry.estimated_max_seconds / 60)} min
            </Text>
          </View>
          <Text style={styles.archiveChevron}>Replay →</Text>
        </Pressable>
      ))}
      {isRefetching ? <Text style={styles.note}>Refreshing…</Text> : null}
    </View>
  );
}

function UpcomingList() {
  const { data, isLoading, error, refetch } = useUpcoming({ limit: 14 });
  if (isLoading) return <Loading text="Loading upcoming…" />;
  if (error) {
    return <ErrorBlock message="Couldn't load upcoming." onRetry={() => void refetch()} />;
  }
  const entries = data?.entries ?? [];
  if (entries.length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyTitle}>No upcoming puzzles</Text>
        <Text style={styles.emptyBody}>
          The next daily puzzles haven't been scheduled yet.
        </Text>
      </View>
    );
  }
  return (
    <View style={{ gap: spacing.sm }}>
      <Text style={styles.note}>
        We show only the upcoming difficulty band — never the puzzle itself.
      </Text>
      {entries.map((e) => (
        <View key={e.scheduled_for} style={styles.archiveRow}>
          <Text style={styles.archiveDate}>{formatDate(e.scheduled_for)}</Text>
          <Text style={[styles.archiveMeta, styles.upcomingPill]}>{capitalize(e.difficulty)}</Text>
        </View>
      ))}
    </View>
  );
}

function Loading({ text }: { readonly text: string }) {
  return (
    <View style={styles.empty}>
      <ActivityIndicator />
      <Text style={styles.emptyBody}>{text}</Text>
    </View>
  );
}

function ErrorBlock({ message, onRetry }: { readonly message: string; readonly onRetry: () => void }) {
  return (
    <View style={styles.empty}>
      <Text style={styles.emptyTitle}>Something went wrong</Text>
      <Text style={styles.emptyBody}>{message}</Text>
      <Pressable onPress={onRetry} style={styles.smallButton}>
        <Text style={styles.smallButtonText}>Retry</Text>
      </Pressable>
    </View>
  );
}

interface SegmentedOption<T> {
  readonly label: string;
  readonly value: T;
}

interface SegmentedProps<T> {
  readonly options: readonly SegmentedOption<T>[];
  readonly value: T;
  readonly onChange: (value: T) => void;
}

function Segmented<T>({ options, value, onChange }: SegmentedProps<T>) {
  return (
    <View style={styles.segmented}>
      {options.map((option, idx) => {
        const isActive = option.value === value;
        return (
          <Pressable
            key={idx}
            style={[styles.segment, isActive && styles.segmentActive]}
            onPress={() => onChange(option.value)}
            accessibilityRole="button"
            accessibilityState={{ selected: isActive }}
          >
            <Text style={[styles.segmentText, isActive && styles.segmentTextActive]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

interface ToggleProps {
  readonly value: boolean;
  readonly onChange: (v: boolean) => void;
}

function Toggle({ value, onChange }: ToggleProps) {
  return (
    <Pressable
      onPress={() => onChange(!value)}
      style={[styles.toggle, value && styles.toggleActive]}
      accessibilityRole="switch"
      accessibilityState={{ checked: value }}
    >
      <View style={[styles.toggleKnob, value && styles.toggleKnobActive]} />
    </Pressable>
  );
}

interface SectionProps {
  readonly title: string;
  readonly children: React.ReactNode;
}

function Section({ title, children }: SectionProps) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function formatDate(iso: string): string {
  try {
    const d = new Date(`${iso}T00:00:00Z`);
    return d.toLocaleDateString(undefined, {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return iso;
  }
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg, backgroundColor: colors.bg, gap: spacing.md },
  gameWrap: { flex: 1, backgroundColor: colors.bg },
  backButton: { padding: spacing.md },
  backText: { color: colors.primary, fontSize: fontSize.md, fontWeight: '600' },
  title: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  subtitle: { fontSize: fontSize.sm, color: colors.textMuted, marginBottom: spacing.sm },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: 2,
  },
  tab: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderRadius: radius.sm,
  },
  tabActive: { backgroundColor: colors.primary },
  tabText: { color: colors.text, fontWeight: '600' },
  tabTextActive: { color: colors.textInverse },
  section: { gap: spacing.sm },
  sectionTitle: {
    fontSize: fontSize.sm,
    fontWeight: '600',
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  segmented: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: 2,
  },
  segment: { flex: 1, paddingVertical: spacing.sm, alignItems: 'center', borderRadius: radius.sm },
  segmentActive: { backgroundColor: colors.primary },
  segmentText: { fontSize: fontSize.md, color: colors.text, fontWeight: '500' },
  segmentTextActive: { color: colors.textInverse, fontWeight: '600' },
  toggle: {
    width: 48,
    height: 28,
    borderRadius: radius.pill,
    backgroundColor: colors.surfaceAlt,
    justifyContent: 'center',
    padding: 2,
  },
  toggleActive: { backgroundColor: colors.primary },
  toggleKnob: {
    width: 24,
    height: 24,
    borderRadius: radius.pill,
    backgroundColor: colors.bg,
    alignSelf: 'flex-start',
  },
  toggleKnobActive: { alignSelf: 'flex-end' },
  startButton: {
    marginTop: spacing.md,
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  startButtonText: { color: colors.textInverse, fontWeight: '700', fontSize: fontSize.md },
  archiveRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    gap: spacing.sm,
  },
  archiveDate: { fontSize: fontSize.md, fontWeight: '600', color: colors.text },
  archiveMeta: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },
  archiveChevron: { color: colors.primary, fontWeight: '700' },
  upcomingPill: {
    backgroundColor: colors.surfaceAlt,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radius.pill,
    fontSize: fontSize.xs,
    fontWeight: '600',
    color: colors.text,
    overflow: 'hidden',
  },
  smallButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  smallButtonText: { color: colors.textInverse, fontWeight: '700' },
  empty: {
    backgroundColor: colors.surface,
    padding: spacing.lg,
    borderRadius: radius.md,
    gap: spacing.sm,
    alignItems: 'center',
  },
  emptyTitle: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  emptyBody: { fontSize: fontSize.sm, color: colors.textMuted, textAlign: 'center' },
  note: { fontSize: fontSize.xs, color: colors.textMuted, lineHeight: 16 },
});

export default PlayScreen;
