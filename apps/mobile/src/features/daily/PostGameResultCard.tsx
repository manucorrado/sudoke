/**
 * Post-game result card (PRD §17).
 *
 * Composition order is intentional and matches the PRD:
 *
 *   1. Completion headline (status, official time, mistakes)
 *   2. Rank + percentile + rating impact
 *   3. Challenge / share CTA placeholder (wired by Epic 6)
 *   4. Leaderboard preview (link to Leaderboard tab)
 *   5. Optional ad slot (Epic 9) — intentionally never the first card.
 *
 * The card is shown after `provisional_ranked`/`validated`/`under_review`.
 * Renders as much as it has — projected delta may take a tick to arrive
 * after submission while the cohort is small.
 */

import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import type { AttemptDTO, MyResultDTO } from '@/lib/sdk';
import { TierBadge } from '@/features/rating/TierBadge';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface PostGameResultCardProps {
  readonly attempt: AttemptDTO;
  readonly myResult: MyResultDTO | null | undefined;
  readonly isLoading: boolean;
  readonly onShareChallenge?: () => void;
  readonly isGuest?: boolean;
  /**
   * Opens the sign-in flow. When provided alongside `isGuest`, the card
   * surfaces a "Sign in to save & be ranked" CTA so guests have a clear
   * path to a permanent rating (PRD §4.2, §5).
   */
  readonly onSignIn?: () => void;
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.round(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function percentileLabel(percentile: number | null): string {
  if (percentile === null) return '—';
  if (percentile >= 99) return 'Top 1%';
  if (percentile >= 95) return 'Top 5%';
  if (percentile >= 90) return 'Top 10%';
  if (percentile >= 75) return 'Top 25%';
  if (percentile >= 50) return 'Top 50%';
  return `${Math.round(percentile)}th percentile`;
}

export function PostGameResultCard({
  attempt,
  myResult,
  isLoading,
  onShareChallenge,
  isGuest = false,
  onSignIn,
}: PostGameResultCardProps) {
  const router = useRouter();
  const isUnderReview = attempt.status === 'under_review';
  const time = attempt.official_duration_ms ?? myResult?.official_duration_ms ?? null;
  const rank = myResult?.rank ?? null;
  const cohort = myResult?.cohort_size ?? 0;
  const delta = myResult?.rating_delta ?? null;
  const ratingAfter = myResult?.rating_after ?? null;
  const tier = myResult?.tier ?? null;

  return (
    <View style={styles.card}>
      <Text style={styles.kicker}>Today's result</Text>
      <Text style={styles.title}>
        {isUnderReview ? 'Under review' : 'Solved!'}
      </Text>

      <View style={styles.metaRow}>
        <View style={styles.metaCell}>
          <Text style={styles.metaLabel}>Time</Text>
          <Text style={styles.metaValue}>{time !== null ? formatDuration(time) : '—'}</Text>
        </View>
        <View style={styles.metaCell}>
          <Text style={styles.metaLabel}>Mistakes</Text>
          <Text style={styles.metaValue}>{attempt.mistakes}</Text>
        </View>
        <View style={styles.metaCell}>
          <Text style={styles.metaLabel}>Rank</Text>
          <Text style={styles.metaValue}>
            {rank !== null ? `${rank} / ${cohort}` : '—'}
          </Text>
        </View>
      </View>

      {isUnderReview ? (
        <Text style={styles.underReview}>
          Your result is being reviewed and isn't currently eligible for ranking.
        </Text>
      ) : null}

      {isLoading ? <ActivityIndicator color={colors.primary} /> : null}

      {isGuest && onSignIn ? (
        <Pressable
          style={styles.guestCta}
          onPress={onSignIn}
          accessibilityRole="button"
          accessibilityLabel="Sign in to save and rank this result"
        >
          <View style={styles.guestCtaTextWrap}>
            <Text style={styles.guestCtaTitle}>Sign in to save & be ranked</Text>
            <Text style={styles.guestCtaSubtitle}>
              Guest results are not on the leaderboard. Create an account to claim this time.
            </Text>
          </View>
          <Text style={styles.guestCtaChevron}>→</Text>
        </Pressable>
      ) : null}

      {!isUnderReview && !isGuest && myResult ? (
        <View style={styles.ratingBlock}>
          <Text style={styles.ratingLabel}>
            {myResult.is_final ? 'Final rating impact' : 'Projected rating impact'}
          </Text>
          <View style={styles.ratingRow}>
            {tier !== null && ratingAfter !== null ? (
              <TierBadge tier={tier} rating={ratingAfter} provisional={myResult.was_provisional} />
            ) : null}
            {delta !== null ? (
              <Text
                style={[styles.delta, delta >= 0 ? styles.deltaUp : styles.deltaDown]}
              >
                {delta > 0 ? '+' : ''}
                {delta}
              </Text>
            ) : null}
          </View>
          <Text style={styles.percentile}>{percentileLabel(myResult.percentile)}</Text>
        </View>
      ) : null}

      <View style={styles.ctaRow}>
        {onShareChallenge ? (
          <Pressable
            style={[styles.cta, styles.ctaPrimary]}
            onPress={onShareChallenge}
            accessibilityRole="button"
          >
            <Text style={styles.ctaPrimaryText}>Challenge a friend</Text>
          </Pressable>
        ) : null}
        <Pressable
          style={[styles.cta, styles.ctaSecondary]}
          onPress={() => router.push('/leaderboard')}
          accessibilityRole="button"
        >
          <Text style={styles.ctaSecondaryText}>View leaderboard</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    padding: spacing.lg,
    borderRadius: radius.lg,
    gap: spacing.sm,
  },
  kicker: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    fontWeight: '600',
  },
  title: { fontSize: fontSize.xl, fontWeight: '700', color: colors.text },
  metaRow: { flexDirection: 'row', gap: spacing.md, marginTop: spacing.sm },
  metaCell: { flex: 1 },
  metaLabel: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    fontWeight: '600',
  },
  metaValue: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text },
  underReview: {
    color: colors.warning,
    fontSize: fontSize.sm,
    marginTop: spacing.xs,
  },
  ratingBlock: {
    marginTop: spacing.sm,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    gap: spacing.xs,
  },
  ratingLabel: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    fontWeight: '600',
  },
  ratingRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  delta: { fontSize: fontSize.lg, fontWeight: '700' },
  deltaUp: { color: colors.success },
  deltaDown: { color: colors.danger },
  percentile: { fontSize: fontSize.sm, color: colors.textMuted },
  ctaRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.md,
    flexWrap: 'wrap',
  },
  cta: {
    flex: 1,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
    minWidth: 140,
  },
  ctaPrimary: { backgroundColor: colors.primary },
  ctaSecondary: { backgroundColor: colors.bg, borderWidth: 1, borderColor: colors.border },
  ctaPrimaryText: { color: colors.textInverse, fontWeight: '700', fontSize: fontSize.md },
  ctaSecondaryText: { color: colors.text, fontWeight: '700', fontSize: fontSize.md },
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
