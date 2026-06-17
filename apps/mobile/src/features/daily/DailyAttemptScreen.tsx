import { useMemo, useRef, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import {
  makeRankedRules,
  parseGridString,
  serializeGrid,
  solve,
  type GameState,
  type Puzzle,
  type PuzzleDifficulty,
} from '@sudoke/sudoku-core';
import { sdk, type AttemptDTO, type DailyPuzzleDTO } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';
import { GameScreen } from '@/features/game/GameScreen';

interface DailyAttemptScreenProps {
  readonly daily: DailyPuzzleDTO;
  readonly attempt: AttemptDTO;
  readonly onExit: () => void;
  readonly onCompleted: (result: AttemptDTO) => void;
}

function buildPuzzleFromDaily(daily: DailyPuzzleDTO): Puzzle {
  // The API guarantees daily puzzles have a unique solution (admin import
  // validates this). We derive the solution client-side from the givens so
  // the engine can enforce immediate wrong-answer detection (§8.1) without
  // sending the solution over the wire. Server still re-validates on submit.
  const givens = parseGridString(daily.givens);
  const solution = solve(givens);
  if (!solution) {
    throw new Error(`Daily puzzle ${daily.id} has no solution`);
  }
  return {
    id: daily.id,
    givens,
    solution,
    metadata: {
      difficulty: daily.difficulty,
      estimatedSolveTimeSeconds: {
        min: daily.estimated_min_seconds,
        max: daily.estimated_max_seconds,
      },
      source: 'Daily',
    },
  };
}

/**
 * Live ranked daily attempt screen.
 *
 * Server owns timing; this component only renders the engine and posts
 * submit/abandon when the local board reaches a terminal state.
 *
 * NOTE: PRD §25.3 says the official timer is server-owned. Because we
 * don't have a "validate cell" endpoint yet, the local engine uses a
 * placeholder solution and skips correctness-based locking — final grid
 * is what the server validates on submit. The mobile UI still tracks
 * mistake count via wrong-entry detection that the player provides
 * directly (number pad). This is a pragmatic MVP shortcut until Epic 4
 * adds the per-cell validator.
 */
export function DailyAttemptScreen({ daily, attempt, onExit, onCompleted }: DailyAttemptScreenProps) {
  const { authCtx } = useAuth();
  const puzzle = useMemo(() => buildPuzzleFromDaily(daily), [daily]);
  const submitting = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AttemptDTO | null>(null);

  async function handleTerminal(state: GameState) {
    if (submitting.current) return;
    submitting.current = true;
    setError(null);
    try {
      if (state.status === 'completed') {
        const submitted = serializeGrid(
          state.grid.map((cell) => cell.value ?? 0),
        );
        const response = await sdk.submitAttempt(
          attempt.id,
          { submitted_grid: submitted, mistakes: state.mistakes },
          authCtx,
        );
        setResult(response);
        onCompleted(response);
      } else if (state.status === 'failed' || state.status === 'abandoned') {
        const response = await sdk.abandonAttempt(attempt.id, authCtx);
        setResult(response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed');
    } finally {
      submitting.current = false;
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <Pressable onPress={onExit} accessibilityRole="button">
          <Text style={styles.exitText}>← Today</Text>
        </Pressable>
        <Text style={styles.difficulty}>{daily.difficulty.toUpperCase()}</Text>
      </View>

      <GameScreen
        initial={{
          puzzle,
          rules: makeRankedRules(),
        }}
        onTerminal={handleTerminal}
        title="Daily Ranked"
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}
      {result ? <Text style={styles.success}>Saved — status: {result.status}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, paddingTop: spacing.md },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  exitText: { color: colors.primary, fontWeight: '600', fontSize: fontSize.md },
  difficulty: {
    fontSize: fontSize.xs,
    fontWeight: '700',
    color: colors.textMuted,
    letterSpacing: 1,
  },
  error: {
    backgroundColor: colors.dangerMuted,
    color: colors.danger,
    padding: spacing.sm,
    margin: spacing.md,
    borderRadius: radius.md,
  },
  success: {
    backgroundColor: colors.successMuted,
    color: colors.success,
    padding: spacing.sm,
    margin: spacing.md,
    borderRadius: radius.md,
  },
});

interface PuzzlePreviewProps {
  readonly daily: DailyPuzzleDTO;
}

/** Pre-attempt preview card per §7.4. */
export function DailyPuzzlePreview({ daily }: PuzzlePreviewProps) {
  const grid = useMemo(() => Array.from(daily.givens), [daily.givens]);
  return (
    <View style={previewStyles.previewCard}>
      <View style={previewStyles.previewBoard}>
        {grid.map((ch, i) => {
          const row = Math.floor(i / 9);
          const col = i % 9;
          return (
            <View
              key={i}
              style={[
                previewStyles.previewCell,
                col % 3 === 0 && col !== 0 && previewStyles.previewCellBoxLeft,
                row % 3 === 0 && row !== 0 && previewStyles.previewCellBoxTop,
              ]}
            >
              {ch !== '0' && ch !== '.' ? (
                <Text style={previewStyles.previewCellText}>{ch}</Text>
              ) : null}
            </View>
          );
        })}
      </View>
    </View>
  );
}

const PREVIEW_CELL = 18;
const previewStyles = StyleSheet.create({
  previewCard: { alignItems: 'center' },
  previewBoard: {
    width: PREVIEW_CELL * 9,
    height: PREVIEW_CELL * 9,
    flexDirection: 'row',
    flexWrap: 'wrap',
    borderWidth: 1.5,
    borderColor: colors.borderStrong,
  },
  previewCell: {
    width: PREVIEW_CELL,
    height: PREVIEW_CELL,
    alignItems: 'center',
    justifyContent: 'center',
    borderRightWidth: 0.5,
    borderBottomWidth: 0.5,
    borderColor: colors.border,
  },
  previewCellBoxLeft: { borderLeftWidth: 1, borderLeftColor: colors.borderStrong },
  previewCellBoxTop: { borderTopWidth: 1, borderTopColor: colors.borderStrong },
  previewCellText: { fontSize: 11, fontWeight: '600', color: colors.text },
});

/** Display-friendly difficulty label. */
export function difficultyLabel(d: PuzzleDifficulty): string {
  return d.charAt(0).toUpperCase() + d.slice(1);
}
