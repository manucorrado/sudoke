import { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import {
  applyAutoFillNotes,
  createGame,
  FIXTURE_PUZZLES,
  makeCasualRules,
  type CasualOverrides,
  type CreateGameInput,
  type GameState,
  type PuzzleDifficulty,
} from '@sudoke/sudoku-core';
import { GameScreen } from '@/features/game/GameScreen';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

const DIFFICULTY_OPTIONS: readonly PuzzleDifficulty[] = ['easy', 'medium', 'hard'];

const MISTAKE_OPTIONS: readonly { label: string; value: number | null }[] = [
  { label: '3', value: 3 },
  { label: '5', value: 5 },
  { label: '∞', value: null },
];

export function PlayScreen() {
  const [difficulty, setDifficulty] = useState<PuzzleDifficulty>('easy');
  const [overrides, setOverrides] = useState<CasualOverrides>({
    maxMistakes: 3,
    hintsEnabled: false,
    autoFillNotes: false,
    autoClearNotes: true,
  });
  const [active, setActive] = useState<CreateGameInput | null>(null);

  const puzzle = useMemo(
    () => FIXTURE_PUZZLES.find((p) => p.metadata.difficulty === difficulty) ?? FIXTURE_PUZZLES[0]!,
    [difficulty],
  );

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
    setActive(seedState ? { ...next, seedState } as CreateGameInput & { seedState: GameState } : next);
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Casual Play</Text>
      <Text style={styles.subtitle}>
        Practice with adjustable settings. Casual results don't affect your rating.
      </Text>

      <Section title="Difficulty">
        <Segmented
          options={DIFFICULTY_OPTIONS.map((d) => ({ label: capitalize(d), value: d }))}
          value={difficulty}
          onChange={setDifficulty}
        />
      </Section>

      <Section title="Mistake limit">
        <Segmented
          options={MISTAKE_OPTIONS}
          value={overrides.maxMistakes ?? null}
          onChange={(v) => setOverrides((prev) => ({ ...prev, maxMistakes: v }))}
        />
      </Section>

      <Section title="Auto-clear notes">
        <Toggle
          value={overrides.autoClearNotes ?? true}
          onChange={(v) => setOverrides((prev) => ({ ...prev, autoClearNotes: v }))}
        />
      </Section>

      <Section title="Auto-fill notes (casual only)">
        <Toggle
          value={overrides.autoFillNotes ?? false}
          onChange={(v) => setOverrides((prev) => ({ ...prev, autoFillNotes: v }))}
        />
      </Section>

      <Section title="Hints (casual only)">
        <Toggle
          value={overrides.hintsEnabled ?? false}
          onChange={(v) => setOverrides((prev) => ({ ...prev, hintsEnabled: v }))}
        />
      </Section>

      <Pressable style={styles.startButton} onPress={handleStart}>
        <Text style={styles.startButtonText}>Start Game</Text>
      </Pressable>
    </ScrollView>
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
            <Text style={[styles.segmentText, isActive && styles.segmentTextActive]}>
              {option.label}
            </Text>
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

const styles = StyleSheet.create({
  container: {
    padding: spacing.lg,
    backgroundColor: colors.bg,
    gap: spacing.md,
  },
  gameWrap: { flex: 1, backgroundColor: colors.bg },
  backButton: { padding: spacing.md },
  backText: { color: colors.primary, fontSize: fontSize.md, fontWeight: '600' },
  title: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  subtitle: { fontSize: fontSize.sm, color: colors.textMuted, marginBottom: spacing.md },
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
  segment: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderRadius: radius.sm,
  },
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
});

export default PlayScreen;
