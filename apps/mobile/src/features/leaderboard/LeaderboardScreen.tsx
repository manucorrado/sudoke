import { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import type { LeaderboardRowDTO, LeaderboardView } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';
import { useDailyPuzzle } from '@/features/daily/useDailyPuzzle';
import { TierBadge } from '@/features/rating/TierBadge';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';
import { useDailyLeaderboard } from './useLeaderboard';

const VIEWS: ReadonlyArray<{ key: LeaderboardView; label: string }> = [
  { key: 'global', label: 'Global' },
  { key: 'nearby', label: 'Nearby' },
  { key: 'friends', label: 'Friends' },
] as const;

function formatDuration(ms: number): string {
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function LeaderboardRow({ row }: { readonly row: LeaderboardRowDTO }) {
  const name = row.display_name ?? row.username ?? 'Player';
  return (
    <View
      style={[styles.row, row.is_me && styles.rowMe]}
      accessibilityLabel={`Rank ${row.rank}, ${name}, ${formatDuration(row.official_duration_ms)}`}
    >
      <Text style={[styles.rank, row.is_me && styles.rankMe]}>{row.rank}</Text>
      <View style={styles.rowMain}>
        <Text style={styles.name} numberOfLines={1}>
          {name}
        </Text>
        <TierBadge tier={row.tier} rating={row.rating} />
      </View>
      <View style={styles.rowMeta}>
        <Text style={styles.time}>{formatDuration(row.official_duration_ms)}</Text>
        {row.rating_delta !== null ? (
          <Text
            style={[
              styles.delta,
              row.rating_delta > 0 ? styles.deltaUp : styles.deltaDown,
            ]}
          >
            {row.rating_delta > 0 ? '+' : ''}
            {row.rating_delta}
          </Text>
        ) : null}
      </View>
    </View>
  );
}

export function LeaderboardScreen() {
  const { status: authStatus } = useAuth();
  const router = useRouter();
  const daily = useDailyPuzzle();
  const [view, setView] = useState<LeaderboardView>('global');
  const dailyId = daily.data?.id;
  const leaderboard = useDailyLeaderboard(dailyId, view);

  if (daily.isLoading) {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (!daily.data) {
    return (
      <View style={[styles.container, styles.center]}>
        <Text style={styles.title}>No daily puzzle</Text>
        <Text style={styles.subtitle}>The leaderboard will appear once a puzzle is live.</Text>
      </View>
    );
  }

  const isGuest = authStatus !== 'authenticated';

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={leaderboard.isFetching}
          onRefresh={() => leaderboard.refetch()}
        />
      }
    >
      <Text style={styles.kicker}>Today's Leaderboard</Text>
      <Text style={styles.title}>
        {leaderboard.data?.is_final ? 'Final results' : 'Live cohort'}
      </Text>
      <Text style={styles.subtitle}>
        {leaderboard.data
          ? `${leaderboard.data.cohort_size} players completed`
          : 'Loading cohort…'}
      </Text>

      <View style={styles.tabRow}>
        {VIEWS.map((v) => {
          const disabled = isGuest && v.key !== 'global';
          const active = view === v.key;
          return (
            <Pressable
              key={v.key}
              onPress={() => !disabled && setView(v.key)}
              style={[
                styles.tab,
                active && styles.tabActive,
                disabled && styles.tabDisabled,
              ]}
              accessibilityRole="button"
              accessibilityState={{ selected: active, disabled }}
            >
              <Text
                style={[
                  styles.tabLabel,
                  active && styles.tabLabelActive,
                  disabled && styles.tabLabelDisabled,
                ]}
              >
                {v.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {leaderboard.isLoading ? (
        <ActivityIndicator color={colors.primary} />
      ) : null}

      {leaderboard.isError ? (
        <Text style={styles.error}>Couldn't load leaderboard.</Text>
      ) : null}

      {leaderboard.data && leaderboard.data.rows.length === 0 ? (
        <Text style={styles.empty}>
          {view === 'friends'
            ? 'No friends have completed today yet.'
            : 'Be the first to complete today\u2019s puzzle.'}
        </Text>
      ) : null}

      <View style={styles.rows}>
        {leaderboard.data?.rows.map((row) => (
          <LeaderboardRow key={`${row.rank}-${row.user_id}`} row={row} />
        ))}
      </View>

      {isGuest ? (
        <Pressable
          onPress={() => router.push('/sign-in')}
          style={styles.guestCta}
          accessibilityRole="button"
          accessibilityLabel="Sign in to see nearby rank, friends, and rating delta"
        >
          <View style={styles.guestCtaTextWrap}>
            <Text style={styles.guestCtaTitle}>Sign in to be ranked</Text>
            <Text style={styles.guestCtaSubtitle}>
              Unlock your nearby rank, friends view, and rating delta.
            </Text>
          </View>
          <Text style={styles.guestCtaChevron}>→</Text>
        </Pressable>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg, backgroundColor: colors.bg, gap: spacing.md, flexGrow: 1 },
  center: { alignItems: 'center', justifyContent: 'center' },
  kicker: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    fontWeight: '600',
  },
  title: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  subtitle: { fontSize: fontSize.md, color: colors.textMuted },
  tabRow: { flexDirection: 'row', gap: spacing.xs },
  tab: {
    flex: 1,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    alignItems: 'center',
  },
  tabActive: { backgroundColor: colors.primary },
  tabDisabled: { opacity: 0.45 },
  tabLabel: { fontSize: fontSize.sm, color: colors.text, fontWeight: '600' },
  tabLabelActive: { color: colors.textInverse },
  tabLabelDisabled: { color: colors.textMuted },
  rows: { gap: spacing.xs },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    gap: spacing.md,
  },
  rowMe: { backgroundColor: colors.primaryMuted },
  rank: {
    fontSize: fontSize.lg,
    fontWeight: '700',
    color: colors.textMuted,
    width: 32,
    textAlign: 'center',
  },
  rankMe: { color: colors.primary },
  rowMain: { flex: 1, gap: spacing.xs },
  name: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  rowMeta: { alignItems: 'flex-end', gap: spacing.xs },
  time: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  delta: { fontSize: fontSize.xs, fontWeight: '700' },
  deltaUp: { color: colors.success },
  deltaDown: { color: colors.danger },
  error: { color: colors.danger, fontSize: fontSize.sm },
  empty: { color: colors.textMuted, fontSize: fontSize.sm, fontStyle: 'italic' },
  guestCta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.primaryMuted,
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.sm,
  },
  guestCtaTextWrap: { flex: 1, gap: 2 },
  guestCtaTitle: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  guestCtaSubtitle: { fontSize: fontSize.xs, color: colors.textMuted, lineHeight: 16 },
  guestCtaChevron: { fontSize: fontSize.lg, fontWeight: '700', color: colors.primary },
});

export default LeaderboardScreen;
