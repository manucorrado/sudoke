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
import { Countdown } from '@/features/daily/Countdown';
import {
  DailyAttemptScreen,
  DailyPuzzlePreview,
} from '@/features/daily/DailyAttemptScreen';
import { useDailyPuzzle } from '@/features/daily/useDailyPuzzle';
import { sdk, type AttemptDTO } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

type Phase = 'idle' | 'starting' | 'in_attempt' | 'completed';

export function TodayScreen() {
  const { ensureGuest, authCtx, status: authStatus, me } = useAuth();
  const daily = useDailyPuzzle();
  const [phase, setPhase] = useState<Phase>('idle');
  const [attempt, setAttempt] = useState<AttemptDTO | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (daily.isLoading || authStatus === 'loading') {
    return (
      <View style={[styles.container, styles.center]}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (daily.isError) {
    return (
      <View style={[styles.container, styles.center]}>
        <Text style={styles.title}>No daily puzzle yet</Text>
        <Text style={styles.subtitle}>
          The first daily puzzle hasn't been published. Check back soon.
        </Text>
        <Pressable style={styles.cta} onPress={() => daily.refetch()}>
          <Text style={styles.ctaText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  const dailyData = daily.data!;

  if (phase === 'in_attempt' && attempt) {
    return (
      <DailyAttemptScreen
        daily={dailyData}
        attempt={attempt}
        onExit={() => {
          setPhase('idle');
          setAttempt(null);
        }}
        onCompleted={(result) => {
          setAttempt(result);
          setPhase('completed');
        }}
      />
    );
  }

  async function handleStart() {
    setError(null);
    setBusy(true);
    try {
      let ctx = authCtx;
      if (!ctx.guestToken && !ctx.bearer) {
        const token = await ensureGuest();
        ctx = { ...ctx, guestToken: token };
      }
      // Preview (does not consume) so the user sees the difficulty pill
      // before committing.
      await sdk.previewDaily(dailyData.id, ctx);
      const started = await sdk.startDaily(dailyData.id, ctx);
      setAttempt(started);
      setPhase('in_attempt');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start');
    } finally {
      setBusy(false);
    }
  }

  const scheduledFor = new Date(dailyData.scheduled_for).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={
        <RefreshControl refreshing={daily.isFetching} onRefresh={() => daily.refetch()} />
      }
    >
      <Text style={styles.kicker}>{scheduledFor}</Text>
      <Text style={styles.title}>Today's Ranked Puzzle</Text>

      <View style={styles.metaRow}>
        <View style={styles.metaPill}>
          <Text style={styles.metaPillLabel}>Difficulty</Text>
          <Text style={styles.metaPillValue}>
            {dailyData.difficulty.charAt(0).toUpperCase() + dailyData.difficulty.slice(1)}
          </Text>
        </View>
        <View style={styles.metaPill}>
          <Text style={styles.metaPillLabel}>Typical solve</Text>
          <Text style={styles.metaPillValue}>
            {Math.round(dailyData.estimated_min_seconds / 60)}–
            {Math.round(dailyData.estimated_max_seconds / 60)} min
          </Text>
        </View>
      </View>

      <DailyPuzzlePreview daily={dailyData} />

      <Countdown endsAt={dailyData.finalize_at} />

      {phase === 'completed' && attempt ? (
        <View style={styles.resultCard}>
          <Text style={styles.resultTitle}>Result · {attempt.status.replace('_', ' ')}</Text>
          {attempt.official_duration_ms !== null ? (
            <Text style={styles.resultLine}>
              Official time: {Math.round(attempt.official_duration_ms / 1000)} s
            </Text>
          ) : null}
          <Text style={styles.resultLine}>Mistakes: {attempt.mistakes}</Text>
          {attempt.under_review_reason ? (
            <Text style={styles.resultUnderReview}>
              Your result is under review and is not currently eligible for ranking.
            </Text>
          ) : null}
        </View>
      ) : (
        <Pressable onPress={handleStart} disabled={busy} style={styles.cta}>
          <Text style={styles.ctaText}>
            {busy ? 'Starting…' : me?.is_guest === false ? 'Start ranked attempt' : 'Play (Guest)'}
          </Text>
        </Pressable>
      )}

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {me?.is_guest !== false ? (
        <Text style={styles.guestNote}>
          Guests can play, but rating-eligible results require an account.
        </Text>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: spacing.lg,
    backgroundColor: colors.bg,
    gap: spacing.md,
    flexGrow: 1,
  },
  center: { alignItems: 'center', justifyContent: 'center' },
  kicker: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    fontWeight: '600',
  },
  title: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  subtitle: { fontSize: fontSize.md, color: colors.textMuted, textAlign: 'center' },
  metaRow: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
  metaPill: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.md,
  },
  metaPillLabel: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  metaPillValue: { fontSize: fontSize.md, color: colors.text, fontWeight: '700', marginTop: 2 },
  cta: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  ctaText: { color: colors.textInverse, fontSize: fontSize.md, fontWeight: '700' },
  error: {
    backgroundColor: colors.dangerMuted,
    color: colors.danger,
    padding: spacing.sm,
    borderRadius: radius.md,
  },
  guestNote: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
  resultCard: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.md,
    gap: spacing.xs,
  },
  resultTitle: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text },
  resultLine: { fontSize: fontSize.sm, color: colors.text },
  resultUnderReview: { fontSize: fontSize.sm, color: colors.warning, marginTop: spacing.xs },
});

export default TodayScreen;
