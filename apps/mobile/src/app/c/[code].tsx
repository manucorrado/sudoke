/**
 * Challenge invite landing route (PRD §16, Epic 6).
 *
 * Deep link format: `sudoke://c/{code}` (or `https://sudoke.app/c/{code}`).
 *
 * Resolves the challenge against the API, shows the challenger's time,
 * and lets the recipient either play as guest or sign in first. The
 * code is also persisted so the post-completion claim flow can attach
 * the result to the right challenge.
 */

import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { setPendingChallenge } from '@/features/social/pendingChallenge';
import { useAuth } from '@/providers/auth';
import { useResolveChallenge } from '@/features/social/useSocial';
import { sdk } from '@/lib/sdk';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

export function ChallengeLandingScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ code?: string | string[] }>();
  const rawCode = Array.isArray(params.code) ? params.code[0] : params.code;
  const code = typeof rawCode === 'string' ? rawCode.trim() : '';
  const { authCtx, ensureGuest, status } = useAuth();
  const [busy, setBusy] = useState(false);
  const [dailyMismatch, setDailyMismatch] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const challenge = useResolveChallenge(code || null);

  useEffect(() => {
    if (!code || !challenge.data) return;
    void setPendingChallenge(code, challenge.data);
  }, [challenge.data, code]);

  async function play() {
    if (!challenge.data) return;
    setDailyMismatch(null);
    setError(null);
    setBusy(true);
    try {
      let ctx = authCtx;
      if (status === 'anonymous') {
        const token = await ensureGuest();
        ctx = { ...ctx, guestToken: token };
      }
      const currentDaily = await sdk.getCurrentDaily(ctx);
      if (currentDaily.id !== challenge.data.challenge.daily_puzzle_id) {
        setDailyMismatch(
          `This challenge was for ${challenge.data.daily_scheduled_for}. Today's puzzle is different.`,
        );
        return;
      }
      await setPendingChallenge(code, challenge.data);
      router.replace('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start this challenge.');
    } finally {
      setBusy(false);
    }
  }

  if (!code) {
    return (
      <View style={[styles.container, styles.center]}>
        <Text style={styles.title}>Challenge link missing code</Text>
        <Text style={styles.subtitle}>Ask your friend to resend the link.</Text>
        <Pressable style={styles.button} onPress={() => router.replace('/')}>
          <Text style={styles.buttonText}>Continue to Sudoke</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.kicker}>Challenge invite</Text>
      <Text style={styles.title}>You've been challenged!</Text>
      {challenge.isLoading ? (
        <ActivityIndicator />
      ) : challenge.data ? (
        <View style={styles.detailCard}>
          <Text style={styles.detailTitle}>
            {challenge.data.challenge.challenger_display_name ||
              challenge.data.challenge.challenger_username ||
              'A friend'}{' '}
            challenged you
          </Text>
          <Text style={styles.subtitle}>
            {challenge.data.daily_difficulty.toUpperCase()} ·{' '}
            {challenge.data.daily_scheduled_for}
          </Text>
          {challenge.data.challenge.challenger_duration_ms !== null ? (
            <Text style={styles.detailLine}>
              Their time: {formatDuration(challenge.data.challenge.challenger_duration_ms)}
              {challenge.data.challenge.challenger_mistakes !== null
                ? ` · ${challenge.data.challenge.challenger_mistakes} mistakes`
                : ''}
            </Text>
          ) : (
            <Text style={styles.detailLine}>They haven't finished yet — beat them to it!</Text>
          )}
        </View>
      ) : (
        <Text style={styles.subtitle}>
          We couldn't resolve this challenge right now. Check the link or ask your friend to
          resend it.
        </Text>
      )}

      <View style={styles.codeCard} accessibilityLabel={`Challenge code ${code}`}>
        <Text style={styles.codeLabel}>Challenge code</Text>
        <Text style={styles.codeValue}>{code}</Text>
      </View>

      <Pressable
        style={[styles.button, busy && styles.buttonDisabled]}
        onPress={play}
        disabled={busy || !challenge.data}
        accessibilityRole="button"
      >
        {busy ? (
          <ActivityIndicator color={colors.textInverse} />
        ) : (
          <Text style={styles.buttonText}>
            {status === 'authenticated' ? 'Play challenge' : 'Play as guest'}
          </Text>
        )}
      </Pressable>
      {status === 'authenticated' ? null : (
        <Pressable
          style={[styles.button, styles.buttonSecondary]}
          onPress={() => router.replace('/sign-in')}
        >
          <Text style={styles.buttonSecondaryText}>Sign in first</Text>
        </Pressable>
      )}

      {dailyMismatch ? <Text style={styles.error}>{dailyMismatch}</Text> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Text style={styles.note}>
        Finish today's puzzle and we'll record your result against this challenge automatically.
      </Text>
    </View>
  );
}

function formatDuration(ms: number): string {
  const total = Math.round(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

export default ChallengeLandingScreen;

const styles = StyleSheet.create({
  container: { flex: 1, padding: spacing.xl, backgroundColor: colors.bg, gap: spacing.md },
  center: { alignItems: 'center', justifyContent: 'center' },
  kicker: {
    fontSize: fontSize.xs,
    color: colors.primary,
    textTransform: 'uppercase',
    fontWeight: '700',
    letterSpacing: 2,
  },
  title: { fontSize: fontSize.xxl, fontWeight: '800', color: colors.text },
  subtitle: { fontSize: fontSize.md, color: colors.textMuted, lineHeight: 22 },
  detailCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: 4,
  },
  detailTitle: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text },
  detailLine: { fontSize: fontSize.sm, color: colors.text, marginTop: 4 },
  codeCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 2,
  },
  codeLabel: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    textTransform: 'uppercase',
    fontWeight: '700',
    letterSpacing: 1,
  },
  codeValue: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text, fontFamily: 'monospace' },
  button: {
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
    backgroundColor: colors.primary,
  },
  buttonSecondary: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  buttonText: { color: colors.textInverse, fontWeight: '700', fontSize: fontSize.md },
  buttonSecondaryText: { color: colors.text, fontWeight: '700', fontSize: fontSize.md },
  buttonDisabled: { opacity: 0.6 },
  error: {
    backgroundColor: colors.warningMuted,
    borderRadius: radius.md,
    color: colors.warning,
    padding: spacing.sm,
  },
  note: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: spacing.md },
});
