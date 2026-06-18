import { useEffect, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { sdk, type RatingDTO } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';
import { TierBadge } from '@/features/rating/TierBadge';
import { useOnboarding } from '@/features/onboarding/useOnboarding';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

/**
 * Profile tab — account status, rating, profile edit and settings shell.
 *
 * Sign-in itself lives on `/sign-in` (PRD §5). The Profile tab points
 * unauthenticated users to that route and focuses on:
 *   - account status + rating block (authed)
 *   - editable username / display name (authed)
 *   - settings placeholders (notifications, account management)
 *   - support / legal entry points (Epic 10)
 */
export function ProfileScreen() {
  const router = useRouter();
  const { me, authCtx, status, signOut, refreshMe } = useAuth();
  const { reset: resetOnboarding } = useOnboarding();
  const [username, setUsername] = useState(me?.username ?? '');
  const [displayName, setDisplayName] = useState(me?.display_name ?? '');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    setUsername(me?.username ?? '');
    setDisplayName(me?.display_name ?? '');
  }, [me]);

  const rating = useQuery<RatingDTO>({
    queryKey: ['me', 'rating'],
    queryFn: () => sdk.getMyRating(authCtx),
    enabled: status === 'authenticated',
    staleTime: 30_000,
  });

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
        {status !== 'authenticated' ? (
          <>
            <Text style={styles.note}>
              Account required for ranked submission, leaderboards, rating, and friends.
            </Text>
            <Pressable
              style={styles.signInButton}
              onPress={() => router.push('/sign-in')}
              accessibilityRole="button"
            >
              <Text style={styles.signInButtonText}>Sign in or create account</Text>
            </Pressable>
          </>
        ) : null}
      </View>

      {status === 'authenticated' && rating.data ? (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Competitive rating</Text>
          <View style={styles.ratingRow}>
            <TierBadge
              tier={rating.data.tier}
              rating={rating.data.rating}
              provisional={rating.data.is_provisional}
            />
          </View>
          {rating.data.is_provisional ? (
            <Text style={styles.note}>
              Provisional — {rating.data.provisional_completions}/10 placement puzzles completed.
            </Text>
          ) : null}
        </View>
      ) : null}

      {status === 'authenticated' ? (
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
            placeholder="username"
          />
          <Text style={styles.label}>Display name</Text>
          <TextInput
            value={displayName}
            onChangeText={setDisplayName}
            maxLength={64}
            style={styles.input}
            placeholder="Display name"
          />
          <Pressable
            style={[styles.button, pending && styles.buttonDisabled]}
            onPress={save}
            disabled={pending}
          >
            <Text style={styles.buttonText}>{pending ? 'Saving…' : 'Save'}</Text>
          </Pressable>
        </View>
      ) : null}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notifications</Text>
        <Pressable style={styles.settingsRow} disabled accessibilityRole="button">
          <Text style={styles.settingsRowTitle}>Daily reminder</Text>
          <Text style={styles.settingsRowValueMuted}>Coming in Epic 8</Text>
        </Pressable>
        <Pressable style={styles.settingsRow} disabled accessibilityRole="button">
          <Text style={styles.settingsRowTitle}>Friend challenges</Text>
          <Text style={styles.settingsRowValueMuted}>Coming in Epic 8</Text>
        </Pressable>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <Pressable
          style={styles.settingsRow}
          onPress={() => Linking.openURL('https://example.com/privacy')}
          accessibilityRole="link"
        >
          <Text style={styles.settingsRowTitle}>Privacy policy</Text>
          <Text style={styles.settingsRowValue}>→</Text>
        </Pressable>
        <Pressable
          style={styles.settingsRow}
          onPress={() => Linking.openURL('https://example.com/terms')}
          accessibilityRole="link"
        >
          <Text style={styles.settingsRowTitle}>Terms of service</Text>
          <Text style={styles.settingsRowValue}>→</Text>
        </Pressable>
        <Pressable
          style={styles.settingsRow}
          onPress={() => Linking.openURL('mailto:support@sudoke.app')}
          accessibilityRole="link"
        >
          <Text style={styles.settingsRowTitle}>Support</Text>
          <Text style={styles.settingsRowValue}>→</Text>
        </Pressable>
      </View>

      {status === 'authenticated' ? (
        <Pressable
          style={[styles.button, styles.buttonSecondary]}
          onPress={() => signOut()}
          accessibilityRole="button"
        >
          <Text style={[styles.buttonText, styles.buttonTextSecondary]}>Sign out</Text>
        </Pressable>
      ) : null}

      {__DEV__ ? (
        <Pressable
          style={[styles.button, styles.buttonGhost]}
          onPress={() => {
            void resetOnboarding();
            router.replace('/onboarding');
          }}
          accessibilityRole="button"
        >
          <Text style={styles.buttonGhostText}>Replay onboarding (dev)</Text>
        </Pressable>
      ) : null}

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
  ratingRow: { marginTop: spacing.sm },
  note: { fontSize: fontSize.xs, color: colors.textMuted, marginTop: spacing.sm, lineHeight: 16 },
  signInButton: {
    marginTop: spacing.sm,
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  signInButtonText: { color: colors.textInverse, fontWeight: '700' },
  section: { gap: spacing.sm },
  sectionTitle: {
    fontSize: fontSize.xs,
    fontWeight: '600',
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
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
  buttonGhost: { backgroundColor: 'transparent' },
  buttonDisabled: { opacity: 0.5 },
  buttonText: { color: colors.textInverse, fontWeight: '700' },
  buttonTextSecondary: { color: colors.text },
  buttonGhostText: { color: colors.primary, fontWeight: '600' },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
  },
  settingsRowTitle: { fontSize: fontSize.md, color: colors.text, fontWeight: '600' },
  settingsRowValue: { fontSize: fontSize.md, color: colors.primary, fontWeight: '700' },
  settingsRowValueMuted: { fontSize: fontSize.xs, color: colors.textMuted },
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
