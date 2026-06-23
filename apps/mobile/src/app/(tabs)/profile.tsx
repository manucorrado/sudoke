import { useEffect, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { sdk, type RatingDTO } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';
import { TierBadge } from '@/features/rating/TierBadge';
import { useOnboarding } from '@/features/onboarding/useOnboarding';
import {
  useNotificationPreferences,
  useStreak,
  useUpdateNotificationPreferences,
} from '@/features/streaks/useStreak';
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
  const streak = useStreak();
  const prefs = useNotificationPreferences();
  const updatePrefs = useUpdateNotificationPreferences();

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

      {status === 'authenticated' && streak.data ? (
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Daily streak</Text>
          <Text style={styles.streakValue}>
            {streak.data.current_length} day{streak.data.current_length === 1 ? '' : 's'}
          </Text>
          <Text style={styles.note}>
            Longest streak {streak.data.longest_length} · {streak.data.completions_total} official completions
          </Text>
          <View style={styles.freezeRow}>
            {Array.from({ length: streak.data.max_freezes }).map((_, i) => (
              <View
                key={i}
                style={[
                  styles.freezeChip,
                  i < streak.data!.freezes_held && styles.freezeChipHeld,
                ]}
              >
                <Text
                  style={[
                    styles.freezeChipText,
                    i < streak.data!.freezes_held && styles.freezeChipTextHeld,
                  ]}
                >
                  ❄ {i < streak.data!.freezes_held ? 'Held' : 'Empty'}
                </Text>
              </View>
            ))}
          </View>
          <Text style={styles.note}>
            Earn one freeze per 7 official completions (max {streak.data.max_freezes}). Freezes auto-consume on a missed day.
          </Text>
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

      {status === 'authenticated' ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>
          <NotificationToggle
            label="Daily reminder"
            value={prefs.data?.daily_reminder ?? true}
            disabled={prefs.isLoading || updatePrefs.isPending}
            onChange={(v) => updatePrefs.mutate({ daily_reminder: v })}
          />
          <NotificationToggle
            label="Friend challenged you"
            value={prefs.data?.friend_challenged_you ?? true}
            disabled={prefs.isLoading || updatePrefs.isPending}
            onChange={(v) => updatePrefs.mutate({ friend_challenged_you: v })}
          />
          <NotificationToggle
            label="Someone beat your time"
            value={prefs.data?.beat_your_time ?? true}
            disabled={prefs.isLoading || updatePrefs.isPending}
            onChange={(v) => updatePrefs.mutate({ beat_your_time: v })}
          />
          <NotificationToggle
            label="Final ranking ready"
            value={prefs.data?.final_ranking_ready ?? true}
            disabled={prefs.isLoading || updatePrefs.isPending}
            onChange={(v) => updatePrefs.mutate({ final_ranking_ready: v })}
          />
          <Text style={styles.note}>
            Push delivery requires installing the native notifications module — preferences are saved
            on the server and respected as soon as it ships.
          </Text>
        </View>
      ) : null}

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

interface NotificationToggleProps {
  readonly label: string;
  readonly value: boolean;
  readonly disabled: boolean;
  readonly onChange: (value: boolean) => void;
}

function NotificationToggle({ label, value, disabled, onChange }: NotificationToggleProps) {
  return (
    <View style={styles.settingsRow}>
      <Text style={styles.settingsRowTitle}>{label}</Text>
      <Switch
        value={value}
        onValueChange={onChange}
        disabled={disabled}
        accessibilityLabel={`${label} notifications`}
      />
    </View>
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
  streakValue: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.primary, marginTop: 2 },
  freezeRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  freezeChip: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bg,
  },
  freezeChipHeld: { backgroundColor: colors.primaryMuted, borderColor: colors.primary },
  freezeChipText: { fontSize: fontSize.xs, color: colors.textMuted, fontWeight: '600' },
  freezeChipTextHeld: { color: colors.primary },
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
