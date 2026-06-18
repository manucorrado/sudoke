/**
 * First-launch onboarding (PRD §5).
 *
 * Guest-first: the player can play immediately as a guest with no signup.
 * The "Sign in / Create account" CTA opens the dedicated sign-in route and
 * remains available later from the Profile tab. Onboarding completion is
 * tracked locally so we never show this screen twice.
 */

import { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '@/providers/auth';
import { useOnboarding } from '@/features/onboarding/useOnboarding';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

interface BulletProps {
  readonly title: string;
  readonly body: string;
}

function Bullet({ title, body }: BulletProps) {
  return (
    <View style={styles.bullet}>
      <View style={styles.bulletDot} />
      <View style={styles.bulletBody}>
        <Text style={styles.bulletTitle}>{title}</Text>
        <Text style={styles.bulletText}>{body}</Text>
      </View>
    </View>
  );
}

export function OnboardingScreen() {
  const router = useRouter();
  const { ensureGuest } = useAuth();
  const { markCompleted } = useOnboarding();
  const [busy, setBusy] = useState<null | 'guest' | 'signin'>(null);
  const [error, setError] = useState<string | null>(null);

  async function playAsGuest() {
    setError(null);
    setBusy('guest');
    try {
      await ensureGuest();
      await markCompleted();
      router.replace('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start guest session');
    } finally {
      setBusy(null);
    }
  }

  async function goToSignIn() {
    setError(null);
    setBusy('signin');
    try {
      await markCompleted();
      router.replace('/sign-in');
    } finally {
      setBusy(null);
    }
  }

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      accessibilityLabel="Sudoke onboarding"
    >
      <View style={styles.header}>
        <Text style={styles.kicker}>Sudoke</Text>
        <Text style={styles.title}>One daily puzzle.{'\n'}Everyone, ranked.</Text>
        <Text style={styles.subtitle}>
          A new Sudoku every day. Race the world, climb tiers, and challenge your friends.
        </Text>
      </View>

      <View style={styles.bullets}>
        <Bullet
          title="Daily ranked puzzle"
          body="The same puzzle worldwide. Your time is ranked against everyone who plays."
        />
        <Bullet
          title="Casual & practice anytime"
          body="Unlimited practice with hints, auto-fill notes, and flexible mistake limits."
        />
        <Bullet
          title="Friends & challenges"
          body="Send a puzzle to a friend and compare times — no account needed to play."
        />
      </View>

      <View style={styles.ctas}>
        <Pressable
          style={[styles.cta, styles.ctaPrimary, busy === 'guest' && styles.ctaDisabled]}
          onPress={playAsGuest}
          disabled={busy !== null}
          accessibilityRole="button"
          accessibilityLabel="Play a quick puzzle"
        >
          {busy === 'guest' ? (
            <ActivityIndicator color={colors.textInverse} />
          ) : (
            <Text style={styles.ctaPrimaryText}>Play a quick puzzle</Text>
          )}
        </Pressable>
        <Pressable
          style={[styles.cta, styles.ctaSecondary, busy === 'signin' && styles.ctaDisabled]}
          onPress={goToSignIn}
          disabled={busy !== null}
          accessibilityRole="button"
          accessibilityLabel="Sign in or create account"
        >
          <Text style={styles.ctaSecondaryText}>
            {busy === 'signin' ? 'Opening…' : 'Sign in / Create account'}
          </Text>
        </Pressable>
      </View>

      <Text style={styles.fine}>
        Guests can play and challenge friends. Ranking, leaderboards, and streaks require an
        account.
      </Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}

export default OnboardingScreen;

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: spacing.xl,
    backgroundColor: colors.bg,
    gap: spacing.xl,
    justifyContent: 'space-between',
  },
  header: { gap: spacing.sm },
  kicker: {
    fontSize: fontSize.xs,
    color: colors.primary,
    textTransform: 'uppercase',
    letterSpacing: 2,
    fontWeight: '700',
  },
  title: { fontSize: fontSize.xxl, fontWeight: '800', color: colors.text, lineHeight: 34 },
  subtitle: { fontSize: fontSize.md, color: colors.textMuted, lineHeight: 22 },
  bullets: { gap: spacing.md },
  bullet: { flexDirection: 'row', gap: spacing.md, alignItems: 'flex-start' },
  bulletDot: {
    width: 10,
    height: 10,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
    marginTop: 6,
  },
  bulletBody: { flex: 1, gap: 2 },
  bulletTitle: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  bulletText: { fontSize: fontSize.sm, color: colors.textMuted, lineHeight: 20 },
  ctas: { gap: spacing.sm },
  cta: {
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
    minHeight: 48,
    justifyContent: 'center',
  },
  ctaPrimary: { backgroundColor: colors.primary },
  ctaSecondary: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  ctaDisabled: { opacity: 0.6 },
  ctaPrimaryText: { color: colors.textInverse, fontWeight: '700', fontSize: fontSize.md },
  ctaSecondaryText: { color: colors.text, fontWeight: '700', fontSize: fontSize.md },
  fine: { fontSize: fontSize.xs, color: colors.textMuted, textAlign: 'center' },
  error: {
    backgroundColor: colors.dangerMuted,
    color: colors.danger,
    padding: spacing.sm,
    borderRadius: radius.md,
  },
});
