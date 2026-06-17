import { useEffect, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { sdk } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

/**
 * Profile tab.
 *
 * - Guest: shows the "Create account" CTA + a brief value prop.
 * - Authenticated: shows username, display name, avatar URL editor.
 * - Anonymous (no guest yet): bootstrap a guest session on demand.
 *
 * Real Clerk sign-up / sign-in flows are intentionally stubbed — in
 * production the bearer comes from ClerkProvider's `useAuth().getToken()`
 * call, but the rest of the wiring (bearer storage, /me hydration,
 * profile PATCH) lives here.
 */
export function ProfileScreen() {
  const { me, authCtx, status, ensureGuest, signOut, refreshMe, setBearer } = useAuth();
  const [bearerInput, setBearerInput] = useState('');
  const [username, setUsername] = useState(me?.username ?? '');
  const [displayName, setDisplayName] = useState(me?.display_name ?? '');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    setUsername(me?.username ?? '');
    setDisplayName(me?.display_name ?? '');
  }, [me]);

  async function applyBearer() {
    setError(null);
    setSuccess(null);
    if (!bearerInput.trim()) return;
    await setBearer(bearerInput.trim());
    await refreshMe();
    setSuccess('Signed in.');
    setBearerInput('');
  }

  async function save() {
    setError(null);
    setSuccess(null);
    setPending(true);
    try {
      const payload: { username?: string; display_name?: string } = {};
      if (username && username !== me?.username) payload.username = username;
      if (displayName && displayName !== me?.display_name) payload.display_name = displayName;
      if (Object.keys(payload).length === 0) {
        setSuccess('Nothing to update');
      } else {
        await sdk.updateProfile(payload, authCtx);
        await refreshMe();
        setSuccess('Profile saved.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setPending(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Profile</Text>

      <View style={styles.card}>
        <Text style={styles.cardLabel}>Account status</Text>
        <Text style={styles.cardValue}>
          {status === 'authenticated'
            ? `Signed in${me?.username ? ` as @${me.username}` : ''}`
            : status === 'guest'
              ? 'Playing as Guest'
              : 'No session'}
        </Text>
        {status === 'guest' || status === 'anonymous' ? (
          <Text style={styles.note}>
            Account required for ranked submission, leaderboards, rating, and friends.
          </Text>
        ) : null}
      </View>

      {status !== 'authenticated' ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Sign in</Text>
          <Text style={styles.note}>
            Paste a Clerk JWT to sign in. (Real Clerk sign-in flows wire here in
            Epic 2; the bearer mechanism below works against the API today.)
          </Text>
          <TextInput
            placeholder="paste bearer token"
            value={bearerInput}
            onChangeText={setBearerInput}
            autoCapitalize="none"
            autoCorrect={false}
            style={styles.input}
          />
          <Pressable style={styles.button} onPress={applyBearer}>
            <Text style={styles.buttonText}>Use this token</Text>
          </Pressable>
          {status === 'anonymous' ? (
            <Pressable
              style={[styles.button, styles.buttonSecondary]}
              onPress={() => {
                void ensureGuest();
              }}
            >
              <Text style={[styles.buttonText, styles.buttonTextSecondary]}>
                Continue as guest
              </Text>
            </Pressable>
          ) : null}
        </View>
      ) : (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Profile</Text>
          <Text style={styles.label}>Username</Text>
          <TextInput
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            autoCorrect={false}
            maxLength={32}
            style={styles.input}
          />
          <Text style={styles.label}>Display name</Text>
          <TextInput
            value={displayName}
            onChangeText={setDisplayName}
            maxLength={64}
            style={styles.input}
          />
          <Pressable
            style={[styles.button, pending && styles.buttonDisabled]}
            onPress={save}
            disabled={pending}
          >
            <Text style={styles.buttonText}>{pending ? 'Saving…' : 'Save'}</Text>
          </Pressable>
          <Pressable style={[styles.button, styles.buttonSecondary]} onPress={() => signOut()}>
            <Text style={[styles.buttonText, styles.buttonTextSecondary]}>Sign out</Text>
          </Pressable>
        </View>
      )}

      {error ? <Text style={styles.error}>{error}</Text> : null}
      {success ? <Text style={styles.success}>{success}</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg, gap: spacing.md, backgroundColor: colors.bg, flexGrow: 1 },
  title: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  card: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.md,
    gap: 4,
  },
  cardLabel: {
    fontSize: fontSize.xs,
    color: colors.textMuted,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  cardValue: { fontSize: fontSize.lg, fontWeight: '700', color: colors.text, marginTop: 2 },
  note: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: spacing.sm },
  section: { gap: spacing.sm },
  sectionTitle: {
    fontSize: fontSize.sm,
    fontWeight: '600',
    color: colors.textMuted,
    textTransform: 'uppercase',
  },
  label: { fontSize: fontSize.xs, color: colors.textMuted },
  input: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.sm,
    fontSize: fontSize.md,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
  },
  button: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  buttonSecondary: { backgroundColor: colors.surface },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: colors.textInverse, fontWeight: '700' },
  buttonTextSecondary: { color: colors.text },
  error: {
    backgroundColor: colors.dangerMuted,
    color: colors.danger,
    padding: spacing.sm,
    borderRadius: radius.md,
  },
  success: {
    backgroundColor: colors.successMuted,
    color: colors.success,
    padding: spacing.sm,
    borderRadius: radius.md,
  },
});

export default ProfileScreen;
