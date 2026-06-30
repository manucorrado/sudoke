import {
  ActivityIndicator,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type TextStyle,
} from 'react-native';
import type { LeaderboardRowDTO, MyResultDTO } from '@/lib/sdk';
import { useArchiveMyResult } from '@/features/archive/useArchive';
import { useDailyLeaderboard } from '@/features/leaderboard/useLeaderboard';
import { TierBadge } from '@/features/rating/TierBadge';
import { useAuth } from '@/providers/auth';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface ArchiveResultCardProps {
  readonly dailyPuzzleId: string;
}

/**
 * Read-only summary for a closed daily (PRD §12, Epic 7): the signed-in
 * player's original ranked result (if they played) plus the historical
 * leaderboard snapshot. Never mutates rating or the board.
 */
export function ArchiveResultCard({ dailyPuzzleId }: ArchiveResultCardProps) {
  const { status } = useAuth();
  const isAuthenticated = status === 'authenticated';
  const myResult = useArchiveMyResult(isAuthenticated ? dailyPuzzleId : null);
  const board = useDailyLeaderboard(dailyPuzzleId, 'historical', 10);
  const rows = board.data?.rows ?? [];

  return (
    <View style={styles.wrap}>
      <Text style={styles.kicker}>ORIGINAL DAILY · READ-ONLY</Text>

      {isAuthenticated ? (
        myResult.isLoading ? (
          <View style={styles.card}>
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : myResult.data?.played && myResult.data.result ? (
          <YourResult result={myResult.data.result} />
        ) : (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>You didn't play this day</Text>
            <Text style={styles.muted}>
              You have no ranked result for this daily. Replaying below is
              practice-only and won't be ranked.
            </Text>
          </View>
        )
      ) : (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Sign in to see your original result</Text>
          <Text style={styles.muted}>
            Your rank, time, and rating change from the day you played appear
            here once you're signed in.
          </Text>
        </View>
      )}

      <Text style={styles.sectionTitle}>Historical leaderboard</Text>
      {board.isLoading ? <ActivityIndicator color={colors.primary} /> : null}
      {board.isError ? (
        <Text style={styles.error}>Couldn't load the historical board.</Text>
      ) : null}
      {board.data && rows.length === 0 ? (
        <Text style={styles.muted}>
          No ranked finishers were recorded for this day.
        </Text>
      ) : null}
      <View style={styles.rows}>
        {rows.map((row) => (
          <HistoricalRow key={`${row.rank}-${row.user_id}`} row={row} />
        ))}
      </View>

      <Text style={styles.footnote}>
        Read-only snapshot from the original daily. Archive replays never affect
        your rating or this leaderboard.
      </Text>
    </View>
  );
}

function YourResult({ result }: { readonly result: MyResultDTO }) {
  return (
    <View style={[styles.card, styles.cardMe]}>
      <Text style={styles.cardTitle}>Your original result</Text>
      <View style={styles.statRow}>
        <Stat label="Rank" value={result.rank !== null ? `#${result.rank}` : '—'} />
        <Stat
          label="Time"
          value={
            result.official_duration_ms !== null
              ? formatDuration(result.official_duration_ms)
              : '—'
          }
        />
        <Stat label="Mistakes" value={String(result.mistakes)} />
        {result.rating_delta !== null ? (
          <Stat
            label="Rating"
            value={`${result.rating_delta > 0 ? '+' : ''}${result.rating_delta}`}
            valueStyle={result.rating_delta >= 0 ? styles.deltaUp : styles.deltaDown}
          />
        ) : null}
      </View>
      <View style={styles.metaRow}>
        {result.tier !== null && result.rating_after !== null ? (
          <TierBadge
            tier={result.tier}
            rating={result.rating_after}
            provisional={result.was_provisional}
          />
        ) : null}
        <Text style={styles.muted}>
          {result.percentile !== null
            ? `${Math.round(result.percentile)}th percentile · `
            : ''}
          {result.cohort_size} players
        </Text>
      </View>
    </View>
  );
}

function HistoricalRow({ row }: { readonly row: LeaderboardRowDTO }) {
  const name = row.display_name ?? row.username ?? 'Player';
  return (
    <View
      style={[styles.row, row.is_me && styles.rowMe]}
      accessibilityLabel={`Rank ${row.rank}, ${name}, ${formatDuration(
        row.official_duration_ms,
      )}`}
    >
      <Text style={[styles.rank, row.is_me && styles.rankMe]}>{row.rank}</Text>
      <Text style={styles.name} numberOfLines={1}>
        {row.is_me ? 'You' : name}
      </Text>
      <Text style={styles.time}>{formatDuration(row.official_duration_ms)}</Text>
    </View>
  );
}

interface StatProps {
  readonly label: string;
  readonly value: string;
  readonly valueStyle?: StyleProp<TextStyle>;
}

function Stat({ label, value, valueStyle }: StatProps) {
  return (
    <View style={styles.stat}>
      <Text style={[styles.statValue, valueStyle]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.sm },
  kicker: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.primary,
    letterSpacing: 1.4,
  },
  card: {
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.xs,
  },
  cardMe: { backgroundColor: colors.primaryMuted, borderColor: colors.primaryMuted },
  cardTitle: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  muted: { fontSize: fontSize.xs, color: colors.textMuted, lineHeight: 16 },
  statRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.lg, marginTop: spacing.xs },
  stat: { gap: 2 },
  statValue: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text },
  statLabel: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginTop: spacing.xs,
  },
  deltaUp: { color: colors.success },
  deltaDown: { color: colors.danger },
  sectionTitle: {
    fontSize: fontSize.sm,
    fontWeight: '600',
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: spacing.xs,
  },
  rows: { gap: spacing.xs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    gap: spacing.md,
  },
  rowMe: { backgroundColor: colors.primaryMuted },
  rank: {
    fontSize: fontSize.md,
    fontWeight: '700',
    color: colors.textMuted,
    width: 28,
    textAlign: 'center',
  },
  rankMe: { color: colors.primary },
  name: { flex: 1, fontSize: fontSize.md, fontWeight: '600', color: colors.text },
  time: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  footnote: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    lineHeight: 16,
    marginTop: spacing.xs,
  },
  error: { color: colors.danger, fontSize: fontSize.sm },
});
