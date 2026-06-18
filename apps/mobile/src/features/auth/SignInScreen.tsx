/**
 * Sign-in / Create account screen (PRD §4, §5).
 *
 * Today this screen offers two paths:
 *   1. Dev bearer paste — for backend testing and CI flows. Always available.
 *   2. Clerk sign-in placeholder — rendered when
 *      `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` is set. The actual `<SignIn>`
 *      component from `@clerk/clerk-expo` will be mounted here when keys
 *      are provisioned (see `providers/clerk-bridge.tsx`).
 *
 * On successful sign-in we kick `/me` and route the player back to the
 * Today tab.
 */

import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '@/providers/auth';
import { isClerkConfigured } from '@/providers/clerk-bridge';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

export function SignInScreen() {
  const router = useRouter();
  const { setBearer, refreshMe, ensureGuest, status } = useAuth();
  const [token, setToken] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function applyBearer() {
    setError(null);
    if (!token.trim()) {
      setError('Paste a token first.');
      return;
    }
    setBusy(true);
    try {
      await setBearer(token.trim());
      await refreshMe();
      setToken('');
      router.replace('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign-in failed');
    } finally {
      setBusy(false);
    }
  }

  async function continueAsGuest() {
    setError(null);
    setBusy(true);
    try {
      await ensureGuest();
      router.replace('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start guest session');
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Pressable onPress={() => router.back()} style={styles.backLink} accessibilityRole="link">
        <Text style={styles.backText}>← Back</Text>
      </Pressable>

      <Text style={styles.title}>Sign in to Sudoke</Text>
      <Text style={styles.subtitle}>
        Sign in to be on the leaderboard, keep a streak, and add friends.
      </Text>

      {isClerkConfigured() ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>With Clerk</Text>
          <View style={styles.placeholder}>
            <Text style={styles.placeholderTitle}>Sign-in UI coming up</Text>
            <Text style={styles.placeholderText}>
              Clerk is configured. The hosted sign-in / sign-up flow will mount here.
            </Text>
          </View>
        </View>
      ) : (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Hosted sign-in</Text>
          <View style={styles.placeholder}>
            <Text style={styles.placeholderTitle}>Not configured</Text>
            <Text style={styles.placeholderText}>
              Set <Text style={styles.code}>EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY</Text> to enable
              Clerk-hosted sign-up & sign-in. The dev token flow below works against the API
              right now.
            </Text>
          </View>
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Dev token</Text>
        <Text style={styles.help}>
          Paste a Clerk-compatible JWT (or any token with a <Text style={styles.code}>sub</Text>
          {' '}claim in development) to sign in against the API.
        </Text>
        <TextInput
          value={token}
          onChangeText={setToken}
          placeholder="paste bearer token"
          autoCapitalize="none"
          autoCorrect={false}
          multiline
          style={styles.input}
          accessibilityLabel="Bearer token"
        />
        <Pressable
          style={[styles.button, styles.buttonPrimary, busy && styles.buttonDisabled]}
          onPress={applyBearer}
          disabled={busy}
        >
          <Text style={styles.buttonPrimaryText}>{busy ? 'Signing in…' : 'Sign in'}</Text>
        </Pressable>
      </View>

      {status !== 'guest' && status !== 'authenticated' ? (
        <Pressable style={[styles.button, styles.buttonGhost]} onPress={continueAsGuest}>
          <Text style={styles.buttonGhostText}>Continue as guest</Text>
        </Pressable>
      ) : null}

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </ScrollView>
  );
}

export default SignInScreen;

const styles = StyleSheet.create({
  container: { padding: spacing.lg, backgroundColor: colors.bg, gap: spacing.md, flexGrow: 1 },
  backLink: { alignSelf: 'flex-start', padding: spacing.xs },
  backText: { color: colors.primary, fontSize: fontSize.md, fontWeight: '600' },
  title: { fontSize: fontSize.xxl, fontWeight: '800', color: colors.text },
  subtitle: { fontSize: fontSize.md, color: colors.textMuted },
  section: { gap: spacing.sm },
  sectionTitle: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    textTransform: 'uppercase',
    fontWeight: '700',
    letterSpacing: 1,
  },
  placeholder: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: spacing.xs,
    borderWidth: 1,
    borderColor: colors.border,
  },
  placeholderTitle: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  placeholderText: { fontSize: fontSize.sm, color: colors.textMuted, lineHeight: 20 },
  code: { fontFamily: 'monospace', color: colors.primary },
  help: { fontSize: fontSize.sm, color: colors.textMuted },
  input: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.sm,
    minHeight: 96,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
    fontSize: fontSize.sm,
    textAlignVertical: 'top',
  },
  button: {
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  buttonPrimary: { backgroundColor: colors.primary },
  buttonPrimaryText: { color: colors.textInverse, fontWeight: '700', fontSize: fontSize.md },
  buttonGhost: { backgroundColor: 'transparent' },
  buttonGhostText: { color: colors.primary, fontWeight: '700', fontSize: fontSize.md },
  buttonDisabled: { opacity: 0.5 },
  error: {
    backgroundColor: colors.dangerMuted,
    color: colors.danger,
    padding: spacing.sm,
    borderRadius: radius.md,
  },
});
