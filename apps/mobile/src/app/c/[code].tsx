/**
 * Challenge invite landing route (PRD §16, Epic 6).
 *
 * Deep link format: `sudoke://c/{code}` (or `https://sudoke.app/c/{code}`).
 *
 * For now this is a stub: we parse the code, persist it as a pending
 * challenge so Epic 6's accept/claim flow can pick it up after onboarding
 * or sign-in, and show a friendly placeholder. The full challenge
 * comparison UX is delivered as part of Epic 6 (Social & Challenges).
 */

import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { appStorage, StorageKeys } from '@/lib/storage';
import { useAuth } from '@/providers/auth';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

export function ChallengeLandingScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ code?: string | string[] }>();
  const rawCode = Array.isArray(params.code) ? params.code[0] : params.code;
  const code = typeof rawCode === 'string' ? rawCode.trim() : '';
  const { ensureGuest, status } = useAuth();
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!code) return;
    void appStorage.set(StorageKeys.pendingChallengeCode, code);
  }, [code]);

  async function play() {
    setBusy(true);
    try {
      if (status === 'anonymous') {
        await ensureGuest();
      }
      router.replace('/');
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
      <Text style={styles.subtitle}>
        A friend invited you to play today's puzzle. Take the challenge — you'll see how your
        time compares once you finish.
      </Text>

      <View style={styles.codeCard} accessibilityLabel={`Challenge code ${code}`}>
        <Text style={styles.codeLabel}>Challenge code</Text>
        <Text style={styles.codeValue}>{code}</Text>
      </View>

      <Pressable
        style={[styles.button, busy && styles.buttonDisabled]}
        onPress={play}
        disabled={busy}
        accessibilityRole="button"
      >
        {busy ? (
          <ActivityIndicator color={colors.textInverse} />
        ) : (
          <Text style={styles.buttonText}>Play as guest</Text>
        )}
      </Pressable>
      <Pressable
        style={[styles.button, styles.buttonSecondary]}
        onPress={() => router.replace('/sign-in')}
      >
        <Text style={styles.buttonSecondaryText}>Sign in first</Text>
      </Pressable>

      <Text style={styles.note}>
        Full challenge comparison ships with Epic 6 — your code is saved and will resolve once
        the social flow is live.
      </Text>
    </View>
  );
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
  note: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: spacing.md },
});
