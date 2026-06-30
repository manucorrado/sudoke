import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useQueryClient } from '@tanstack/react-query';
import { Countdown } from '@/features/daily/Countdown';
import {
  DailyAttemptScreen,
  DailyPuzzlePreview,
} from '@/features/daily/DailyAttemptScreen';
import { PostGameResultCard } from '@/features/daily/PostGameResultCard';
import { useDailyPuzzle } from '@/features/daily/useDailyPuzzle';
import {
  myResultKey,
  useMyDailyResult,
} from '@/features/leaderboard/useLeaderboard';
import { ChallengeComparisonCard, type ChallengeOutcome } from '@/features/social/ChallengeComparisonCard';
import { getPendingChallenge } from '@/features/social/pendingChallenge';
import { usePendingChallenge } from '@/features/social/usePendingChallenge';
import { useCreateChallenge } from '@/features/social/useSocial';
import { useRecordChallengeResult } from '@/features/social/useRecordChallengeResult';
import {
  sdk,
  type AttemptDTO,
  type AuthContext,
  type ChallengeAcceptanceDTO,
  type ChallengeDetailDTO,
} from '@/lib/sdk';
import { useAuth } from '@/providers/auth';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

type Phase = 'idle' | 'starting' | 'in_attempt' | 'completed';

export function TodayScreen() {
  const { ensureGuest, authCtx, status: authStatus, me } = useAuth();
  const router = useRouter();
  const isGuest = me?.is_guest !== false;
  const daily = useDailyPuzzle();
  const queryClient = useQueryClient();
  const [phase, setPhase] = useState<Phase>('idle');
  const [attempt, setAttempt] = useState<AttemptDTO | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [challengeRecordError, setChallengeRecordError] = useState<string | null>(null);
  const [challengeMismatch, setChallengeMismatch] = useState<string | null>(null);
  const [challengeAcceptance, setChallengeAcceptance] =
    useState<ChallengeAcceptanceDTO | null>(null);
  const [completedChallenge, setCompletedChallenge] =
    useState<ChallengeDetailDTO | null>(null);
  const [busy, setBusy] = useState(false);
  const createChallenge = useCreateChallenge();
  const recordChallengeResult = useRecordChallengeResult();
  const pendingChallenge = usePendingChallenge(phase !== 'in_attempt');
  const myResult = useMyDailyResult(
    phase === 'completed' ? daily.data?.id : undefined,
  );

  useEffect(() => {
    if (phase === 'completed' && daily.data?.id) {
      // Refresh leaderboard + my-result once the cohort changes.
      queryClient.invalidateQueries({ queryKey: ['leaderboard', daily.data.id] });
      queryClient.invalidateQueries({ queryKey: myResultKey(daily.data.id) });
    }
  }, [phase, daily.data?.id, queryClient]);

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
  const pendingMismatch =
    pendingChallenge.detail !== null &&
    pendingChallenge.detail.challenge.daily_puzzle_id !== dailyData.id;

  if (phase === 'in_attempt' && attempt) {
    return (
      <DailyAttemptScreen
        daily={dailyData}
        attempt={attempt}
        onExit={() => {
          setPhase('idle');
          setAttempt(null);
        }}
        onCompleted={(result) => void handleCompleted(result)}
      />
    );
  }

  async function handleCompleted(result: AttemptDTO) {
    setAttempt(result);
    setPhase('completed');
    setChallengeRecordError(null);
    setChallengeMismatch(null);
    setChallengeAcceptance(null);
    setCompletedChallenge(null);

    await recordPendingChallenge(result);
  }

  async function recordPendingChallenge(result: AttemptDTO) {
    setChallengeRecordError(null);
    setChallengeMismatch(null);

    if (!isRecordableChallengeAttempt(result)) {
      return;
    }

    const storedPending =
      pendingChallenge.code === null ? await getPendingChallenge() : null;
    const pendingCode =
      (pendingChallenge.code ?? storedPending?.code?.trim()) || null;
    if (pendingCode === null) {
      return;
    }

    let detail = pendingChallenge.detail;
    if (detail === null && pendingChallenge.code !== null) {
      detail = (await pendingChallenge.refetch()).data ?? null;
    }
    detail = detail ?? (await resolveChallenge(pendingCode, authCtx));
    if (detail === null) {
      setChallengeRecordError('Challenge details could not be loaded. Try saving again.');
      return;
    }

    if (detail.challenge.daily_puzzle_id !== result.daily_puzzle_id) {
      setChallengeMismatch(
        `This challenge was for ${detail.daily_scheduled_for}. Today's puzzle is different.`,
      );
      return;
    }

    try {
      let ctx: AuthContext = authCtx;
      if (!ctx.bearer && !ctx.guestToken) {
        const token = await ensureGuest();
        ctx = { ...ctx, guestToken: token };
      }
      const acceptance = await recordChallengeResult.mutateAsync({
        challengeId: detail.challenge.id,
        authCtx: ctx,
      });
      setChallengeAcceptance(acceptance);
      setCompletedChallenge(detail);
      await pendingChallenge.clear();
    } catch (err) {
      setChallengeRecordError(
        err instanceof Error ? err.message : 'Challenge result was not saved.',
      );
    }
  }

  async function handleStart() {
    setError(null);
    setChallengeRecordError(null);
    setChallengeMismatch(null);
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

  async function handleShareChallenge() {
    setError(null);
    try {
      const challenge = await createChallenge.mutateAsync({
        daily_puzzle_id: dailyData.id,
      });
      const timeText =
        attempt?.official_duration_ms !== null && attempt?.official_duration_ms !== undefined
          ? formatDuration(attempt.official_duration_ms)
          : "today's daily";
      await Share.share({
        message: `I solved today's Sudoke in ${timeText} — can you beat me? ${challenge.share_url}`,
        url: challenge.share_url,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create challenge');
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
        <>
          <PostGameResultCard
            attempt={attempt}
            myResult={myResult.data ?? null}
            isLoading={myResult.isLoading}
            isGuest={isGuest}
            {...(!isGuest && authStatus === 'authenticated'
              ? { onShareChallenge: handleShareChallenge }
              : {})}
            {...(isGuest ? { onSignIn: () => router.push('/sign-in') } : {})}
          />
          {challengeAcceptance && completedChallenge && challengeAcceptance.duration_ms !== null ? (
            <ChallengeComparisonCard
              challengerName={challengerName(completedChallenge)}
              challengerDurationMs={completedChallenge.challenge.challenger_duration_ms}
              challengerMistakes={completedChallenge.challenge.challenger_mistakes}
              recipientDurationMs={challengeAcceptance.duration_ms}
              recipientMistakes={challengeAcceptance.mistakes ?? attempt.mistakes}
              outcome={challengeOutcome(
                challengeAcceptance.duration_ms,
                challengeAcceptance.mistakes ?? attempt.mistakes,
                completedChallenge.challenge.challenger_duration_ms,
                completedChallenge.challenge.challenger_mistakes,
              )}
            />
          ) : null}
          {challengeMismatch ? <Text style={styles.warning}>{challengeMismatch}</Text> : null}
          {challengeRecordError ? (
            <Text style={styles.error}>{challengeRecordError}</Text>
          ) : null}
          {challengeRecordError ? (
            <Pressable
              style={[styles.secondaryCta, recordChallengeResult.isPending && styles.disabled]}
              disabled={recordChallengeResult.isPending}
              onPress={() => void recordPendingChallenge(attempt)}
              accessibilityRole="button"
            >
              <Text style={styles.secondaryCtaText}>
                {recordChallengeResult.isPending ? 'Saving…' : 'Save challenge result'}
              </Text>
            </Pressable>
          ) : null}
        </>
      ) : (
        <Pressable onPress={handleStart} disabled={busy} style={styles.cta}>
          <Text style={styles.ctaText}>
            {busy ? 'Starting…' : isGuest ? 'Play (Guest)' : 'Start ranked attempt'}
          </Text>
        </Pressable>
      )}

      {phase !== 'completed' && pendingMismatch ? (
        <Text style={styles.warning}>
          This saved challenge was for {pendingChallenge.detail?.daily_scheduled_for}. Today's
          puzzle is different, so it will not be recorded.
        </Text>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {isGuest && phase !== 'completed' ? (
        <Pressable
          onPress={() => router.push('/sign-in')}
          style={styles.guestBanner}
          accessibilityRole="button"
          accessibilityLabel="Sign in to be ranked"
        >
          <View style={styles.guestBannerTextWrap}>
            <Text style={styles.guestBannerTitle}>Sign in to be ranked</Text>
            <Text style={styles.guestBannerSubtitle}>
              Guests can play. Rating, leaderboards, and streaks need an account.
            </Text>
          </View>
          <Text style={styles.guestBannerChevron}>→</Text>
        </Pressable>
      ) : null}
    </ScrollView>
  );
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.round(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function isRecordableChallengeAttempt(attempt: AttemptDTO): boolean {
  if (attempt.official_duration_ms === null) return false;
  return (
    attempt.status === 'validated' ||
    attempt.status === 'provisional_ranked' ||
    attempt.status === 'finalized' ||
    attempt.status === 'under_review'
  );
}

async function resolveChallenge(
  code: string,
  authCtx: AuthContext,
): Promise<ChallengeDetailDTO | null> {
  try {
    return await sdk.resolveChallengeByCode(code, authCtx);
  } catch {
    return null;
  }
}

function challengerName(detail: ChallengeDetailDTO): string {
  return (
    detail.challenge.challenger_display_name ||
    detail.challenge.challenger_username ||
    'Your friend'
  );
}

function challengeOutcome(
  recipientDurationMs: number,
  recipientMistakes: number,
  challengerDurationMs: number | null,
  challengerMistakes: number | null,
): ChallengeOutcome {
  if (challengerDurationMs === null) return 'pending';
  if (recipientDurationMs < challengerDurationMs) return 'win';
  if (recipientDurationMs > challengerDurationMs) return 'lose';
  if (challengerMistakes === null) return 'tie';
  if (recipientMistakes < challengerMistakes) return 'win';
  if (recipientMistakes > challengerMistakes) return 'lose';
  return 'tie';
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
  secondaryCta: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  secondaryCtaText: { color: colors.text, fontSize: fontSize.md, fontWeight: '700' },
  error: {
    backgroundColor: colors.dangerMuted,
    color: colors.danger,
    padding: spacing.sm,
    borderRadius: radius.md,
  },
  disabled: { opacity: 0.6 },
  warning: {
    backgroundColor: colors.warningMuted,
    color: colors.warning,
    padding: spacing.sm,
    borderRadius: radius.md,
  },
  guestBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.primaryMuted,
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.sm,
  },
  guestBannerTextWrap: { flex: 1, gap: 2 },
  guestBannerTitle: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  guestBannerSubtitle: { fontSize: fontSize.xs, color: colors.textMuted, lineHeight: 16 },
  guestBannerChevron: { fontSize: fontSize.lg, fontWeight: '700', color: colors.primary },
});

export default TodayScreen;
