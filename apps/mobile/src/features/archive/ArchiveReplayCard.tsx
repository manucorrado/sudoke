import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import {
  type GameRules,
  type GameState,
  type Puzzle,
  type PuzzleDifficulty,
} from '@sudoke/sudoku-core';
import { GameScreen } from '@/features/game/GameScreen';
import { sdk, type GhostRankDTO } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface ArchiveReplayCardProps {
  readonly dailyPuzzleId: string;
  readonly scheduledFor: string;
  readonly difficulty: PuzzleDifficulty;
  readonly puzzle: Puzzle;
  readonly rules: GameRules;
}

/**
 * Wraps GameScreen for archive replay. Captures end-of-game time +
 * mistakes and surfaces a ghost rank against the original cohort.
 */
export function ArchiveReplayCard(props: ArchiveReplayCardProps) {
  const [terminalState, setTerminalState] = useState<GameState | null>(null);
  const [startedAt] = useState<number>(() => Date.now());
  const [endedAt, setEndedAt] = useState<number | null>(null);

  const onTerminal = (state: GameState) => {
    setTerminalState(state);
    setEndedAt(Date.now());
  };

  return (
    <View style={styles.wrap}>
      <View style={styles.header}>
        <Text style={styles.headerLabel}>Archive · {props.scheduledFor}</Text>
        <Text style={styles.headerSub}>
          Practice replay · {capitalize(props.difficulty)} · unofficial
        </Text>
      </View>

      <GameScreen
        initial={{ puzzle: props.puzzle, rules: props.rules }}
        onTerminal={onTerminal}
      />

      {terminalState && terminalState.status === 'completed' && endedAt !== null ? (
        <GhostRankBanner
          dailyPuzzleId={props.dailyPuzzleId}
          durationMs={endedAt - startedAt}
          mistakes={terminalState.mistakes}
        />
      ) : null}
    </View>
  );
}

interface GhostRankBannerProps {
  readonly dailyPuzzleId: string;
  readonly durationMs: number;
  readonly mistakes: number;
}

function GhostRankBanner({ dailyPuzzleId, durationMs, mistakes }: GhostRankBannerProps) {
  const { authCtx } = useAuth();
  const query = useQuery<GhostRankDTO>({
    queryKey: ['ghost-rank', dailyPuzzleId, durationMs, mistakes],
    queryFn: () =>
      sdk.getGhostRank(
        dailyPuzzleId,
        { duration_ms: durationMs, mistakes },
        authCtx,
      ),
  });

  if (query.isLoading) {
    return (
      <View style={styles.ghostCard}>
        <ActivityIndicator />
        <Text style={styles.ghostBody}>Calculating ghost rank…</Text>
      </View>
    );
  }
  if (query.error || !query.data) {
    return (
      <View style={styles.ghostCard}>
        <Text style={styles.ghostTitle}>Ghost rank unavailable</Text>
        <Text style={styles.ghostBody}>
          We couldn't compare your time to the original cohort.
        </Text>
      </View>
    );
  }
  const d = query.data;
  const seconds = Math.round(d.duration_ms / 1000);
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  return (
    <View style={styles.ghostCard}>
      <Text style={styles.ghostKicker}>UNOFFICIAL · GHOST RANK</Text>
      <Text style={styles.ghostTitle}>
        {d.ghost_rank
          ? `Would have ranked #${d.ghost_rank} of ${d.cohort_size}`
          : d.cohort_size === 0
            ? 'No ranked cohort yet'
            : `Outside top ${d.cohort_size}`}
      </Text>
      <Text style={styles.ghostBody}>
        {`${min}:${String(sec).padStart(2, '0')} · ${mistakes} mistakes`}
        {d.percentile !== null ? ` · ${d.percentile}th percentile` : ''}
      </Text>
      <Text style={styles.ghostFootnote}>
        Archive replays never affect your rating or the historical leaderboard.
      </Text>
    </View>
  );
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

const styles = StyleSheet.create({
  wrap: { flex: 1, gap: spacing.sm, backgroundColor: colors.bg },
  header: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
  },
  headerLabel: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text },
  headerSub: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: 2 },
  ghostCard: {
    margin: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 4,
  },
  ghostKicker: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: 1.4,
  },
  ghostTitle: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  ghostBody: { fontSize: fontSize.sm, color: colors.text },
  ghostFootnote: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    marginTop: spacing.sm,
  },
});
