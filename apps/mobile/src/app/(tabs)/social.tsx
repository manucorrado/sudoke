import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '@/providers/auth';
import {
  useCreateChallenge,
  useFriendActions,
  useFriendRequests,
  useFriends,
  useMyChallenges,
  useSearchUsers,
} from '@/features/social/useSocial';
import type {
  ChallengeDTO,
  FriendDTO,
  FriendRequestDTO,
  UserSearchResultDTO,
} from '@/lib/sdk';
import { colors, fontSize, radius, spacing } from '@/theme/tokens';

type TabKey = 'friends' | 'challenges' | 'search';

const TABS: readonly { key: TabKey; label: string }[] = [
  { key: 'friends', label: 'Friends' },
  { key: 'challenges', label: 'Challenges' },
  { key: 'search', label: 'Find' },
];

export function SocialScreen() {
  const router = useRouter();
  const { status } = useAuth();
  const [tab, setTab] = useState<TabKey>('friends');

  if (status !== 'authenticated') {
    return (
      <View style={styles.gate}>
        <Text style={styles.gateTitle}>Sign in to compete with friends</Text>
        <Text style={styles.gateBody}>
          Friend requests and challenges require an account. You can still play as a guest
          everywhere else.
        </Text>
        <Pressable
          style={styles.primaryButton}
          onPress={() => router.push('/sign-in')}
          accessibilityRole="button"
        >
          <Text style={styles.primaryButtonText}>Sign in or create account</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Social</Text>
      <Text style={styles.subtitle}>
        Friend other players, send Wordle-style challenges, and compare results.
      </Text>

      <View style={styles.tabBar}>
        {TABS.map((t) => {
          const isActive = t.key === tab;
          return (
            <Pressable
              key={t.key}
              onPress={() => setTab(t.key)}
              style={[styles.tab, isActive && styles.tabActive]}
              accessibilityRole="tab"
              accessibilityState={{ selected: isActive }}
            >
              <Text style={[styles.tabText, isActive && styles.tabTextActive]}>{t.label}</Text>
            </Pressable>
          );
        })}
      </View>

      {tab === 'friends' ? <FriendsTab /> : tab === 'challenges' ? <ChallengesTab /> : <SearchTab />}
    </ScrollView>
  );
}

function FriendsTab() {
  const friends = useFriends();
  const requests = useFriendRequests();
  const actions = useFriendActions();
  const incoming = requests.data?.incoming ?? [];
  const outgoing = requests.data?.outgoing ?? [];
  const friendList = friends.data?.friends ?? [];

  return (
    <View style={{ gap: spacing.md }}>
      {incoming.length > 0 ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Pending requests ({incoming.length})</Text>
          {incoming.map((r) => (
            <FriendRequestRow
              key={r.id}
              request={r}
              direction="incoming"
              onAccept={() => actions.accept.mutate(r.id)}
              onDecline={() => actions.decline.mutate(r.id)}
              busy={actions.accept.isPending || actions.decline.isPending}
            />
          ))}
        </View>
      ) : null}

      {outgoing.length > 0 ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Sent ({outgoing.length})</Text>
          {outgoing.map((r) => (
            <FriendRequestRow
              key={r.id}
              request={r}
              direction="outgoing"
              onCancel={() => actions.cancel.mutate(r.id)}
              busy={actions.cancel.isPending}
            />
          ))}
        </View>
      ) : null}

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Friends ({friendList.length})</Text>
        {friends.isLoading ? <ActivityIndicator /> : null}
        {friendList.length === 0 ? (
          <Text style={styles.muted}>
            You haven't added any friends yet. Use the Find tab to search by username.
          </Text>
        ) : (
          friendList.map((f) => <FriendRow key={f.user_id} friend={f} />)
        )}
      </View>
    </View>
  );
}

function FriendRow({ friend }: { readonly friend: FriendDTO }) {
  return (
    <View style={styles.row}>
      <View style={{ flex: 1 }}>
        <Text style={styles.rowTitle}>
          {friend.display_name || friend.username || 'Unknown'}
        </Text>
        {friend.username ? <Text style={styles.muted}>@{friend.username}</Text> : null}
      </View>
    </View>
  );
}

interface FriendRequestRowProps {
  readonly request: FriendRequestDTO;
  readonly direction: 'incoming' | 'outgoing';
  readonly busy?: boolean;
  readonly onAccept?: () => void;
  readonly onDecline?: () => void;
  readonly onCancel?: () => void;
}

function FriendRequestRow({
  request,
  direction,
  busy,
  onAccept,
  onDecline,
  onCancel,
}: FriendRequestRowProps) {
  const name =
    direction === 'incoming'
      ? request.from_display_name || request.from_username || 'Unknown'
      : request.to_display_name || request.to_username || 'Unknown';
  return (
    <View style={styles.row}>
      <View style={{ flex: 1 }}>
        <Text style={styles.rowTitle}>{name}</Text>
        <Text style={styles.muted}>
          {direction === 'incoming' ? 'Wants to be friends' : 'Awaiting reply'}
        </Text>
      </View>
      {direction === 'incoming' ? (
        <View style={{ flexDirection: 'row', gap: spacing.xs }}>
          <Pressable
            style={[styles.smallButton, busy && styles.disabled]}
            onPress={onAccept}
            disabled={busy}
            accessibilityRole="button"
          >
            <Text style={styles.smallButtonText}>Accept</Text>
          </Pressable>
          <Pressable
            style={[styles.smallButtonSecondary, busy && styles.disabled]}
            onPress={onDecline}
            disabled={busy}
            accessibilityRole="button"
          >
            <Text style={styles.smallButtonSecondaryText}>Decline</Text>
          </Pressable>
        </View>
      ) : (
        <Pressable
          style={[styles.smallButtonSecondary, busy && styles.disabled]}
          onPress={onCancel}
          disabled={busy}
          accessibilityRole="button"
        >
          <Text style={styles.smallButtonSecondaryText}>Cancel</Text>
        </Pressable>
      )}
    </View>
  );
}

function SearchTab() {
  const [query, setQuery] = useState('');
  const [debounced, setDebounced] = useState('');
  useEffect(() => {
    const id = setTimeout(() => setDebounced(query.trim()), 250);
    return () => clearTimeout(id);
  }, [query]);
  const search = useSearchUsers(debounced);
  const actions = useFriendActions();
  return (
    <View style={{ gap: spacing.md }}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Find players</Text>
        <TextInput
          value={query}
          onChangeText={setQuery}
          placeholder="Search by username or display name"
          autoCapitalize="none"
          autoCorrect={false}
          style={styles.input}
        />
      </View>
      {search.isLoading && debounced ? <ActivityIndicator /> : null}
      {search.data?.results.map((u) => (
        <UserSearchRow
          key={u.id}
          user={u}
          busy={actions.send.isPending}
          onAdd={() => u.username && actions.send.mutate(u.username)}
        />
      ))}
      {debounced && !search.isLoading && (search.data?.results ?? []).length === 0 ? (
        <Text style={styles.muted}>No players matched "{debounced}".</Text>
      ) : null}
    </View>
  );
}

function UserSearchRow({
  user,
  busy,
  onAdd,
}: {
  readonly user: UserSearchResultDTO;
  readonly busy: boolean;
  readonly onAdd: () => void;
}) {
  return (
    <View style={[styles.card, styles.row]}>
      <View style={{ flex: 1 }}>
        <Text style={styles.rowTitle}>{user.display_name || user.username || 'Unknown'}</Text>
        {user.username ? <Text style={styles.muted}>@{user.username}</Text> : null}
      </View>
      {user.relationship === 'friends' ? (
        <Text style={styles.tagPill}>Friend</Text>
      ) : user.relationship === 'request_sent' ? (
        <Text style={styles.tagPill}>Requested</Text>
      ) : user.relationship === 'request_received' ? (
        <Text style={styles.tagPill}>Wants to add you</Text>
      ) : user.relationship === 'self' ? (
        <Text style={styles.tagPill}>You</Text>
      ) : (
        <Pressable
          style={[styles.smallButton, busy && styles.disabled]}
          onPress={onAdd}
          disabled={busy}
        >
          <Text style={styles.smallButtonText}>Add</Text>
        </Pressable>
      )}
    </View>
  );
}

function ChallengesTab() {
  const challenges = useMyChallenges();
  const create = useCreateChallenge();
  const sent = challenges.data?.sent ?? [];
  const received = challenges.data?.received ?? [];

  async function handleShare(c: ChallengeDTO) {
    try {
      await Share.share({
        message: `I challenged you on Sudoke — try today's puzzle: ${c.share_url}`,
        url: c.share_url,
      });
    } catch {
      /* user cancelled */
    }
  }

  return (
    <View style={{ gap: spacing.md }}>
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Challenge today's daily</Text>
        <Text style={styles.muted}>
          Generates a share link to today's puzzle. Friends who play through your link will see
          their time compared to yours.
        </Text>
        <Pressable
          style={[styles.primaryButton, create.isPending && styles.disabled]}
          onPress={() => create.mutate(undefined)}
          disabled={create.isPending}
        >
          <Text style={styles.primaryButtonText}>
            {create.isPending ? 'Creating…' : 'Create challenge link'}
          </Text>
        </Pressable>
        {create.error ? (
          <Text style={styles.error}>{create.error.message}</Text>
        ) : null}
        {create.data ? (
          <View style={styles.codeCard}>
            <Text style={styles.muted}>Share URL</Text>
            <Text style={styles.codeValue}>{create.data.share_url}</Text>
            <Pressable
              style={styles.smallButton}
              onPress={() => handleShare(create.data!)}
            >
              <Text style={styles.smallButtonText}>Share…</Text>
            </Pressable>
          </View>
        ) : null}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Sent ({sent.length})</Text>
        {sent.length === 0 ? (
          <Text style={styles.muted}>You haven't sent any active challenges yet.</Text>
        ) : (
          sent.map((c) => (
            <ChallengeRow key={c.id} challenge={c} onShare={() => handleShare(c)} />
          ))
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Received ({received.length})</Text>
        {received.length === 0 ? (
          <Text style={styles.muted}>No active challenges from friends.</Text>
        ) : (
          received.map((c) => (
            <ChallengeRow key={c.id} challenge={c} onShare={() => handleShare(c)} />
          ))
        )}
      </View>
    </View>
  );
}

function ChallengeRow({
  challenge,
  onShare,
}: {
  readonly challenge: ChallengeDTO;
  readonly onShare: () => void;
}) {
  return (
    <View style={styles.row}>
      <View style={{ flex: 1 }}>
        <Text style={styles.rowTitle}>
          {challenge.challenger_display_name || challenge.challenger_username || 'You'}
        </Text>
        <Text style={styles.muted}>
          Code {challenge.code}
          {challenge.challenger_duration_ms !== null
            ? ` · ${formatDuration(challenge.challenger_duration_ms)}`
            : ' · result pending'}
        </Text>
      </View>
      <Pressable style={styles.smallButton} onPress={onShare}>
        <Text style={styles.smallButtonText}>Share</Text>
      </Pressable>
    </View>
  );
}

function formatDuration(ms: number): string {
  const total = Math.round(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg, gap: spacing.md, backgroundColor: colors.bg },
  title: { fontSize: fontSize.xxl, fontWeight: '700', color: colors.text },
  subtitle: { fontSize: fontSize.sm, color: colors.textMuted, marginBottom: spacing.sm },
  gate: { flex: 1, padding: spacing.xl, gap: spacing.md, backgroundColor: colors.bg, justifyContent: 'center' },
  gateTitle: { fontSize: fontSize.xl, fontWeight: '700', color: colors.text },
  gateBody: { fontSize: fontSize.md, color: colors.textMuted, lineHeight: 22 },
  tabBar: { flexDirection: 'row', backgroundColor: colors.surface, borderRadius: radius.md, padding: 2 },
  tab: { flex: 1, paddingVertical: spacing.sm, alignItems: 'center', borderRadius: radius.sm },
  tabActive: { backgroundColor: colors.primary },
  tabText: { color: colors.text, fontWeight: '600' },
  tabTextActive: { color: colors.textInverse },
  card: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: radius.md,
    gap: spacing.sm,
  },
  cardTitle: { fontSize: fontSize.md, fontWeight: '700', color: colors.text },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.sm,
    paddingVertical: spacing.xs,
  },
  rowTitle: { fontSize: fontSize.md, fontWeight: '600', color: colors.text },
  muted: { fontSize: fontSize.xs, color: colors.textMuted },
  input: {
    backgroundColor: colors.bg,
    borderRadius: radius.md,
    padding: spacing.sm,
    fontSize: fontSize.md,
    color: colors.text,
    borderWidth: 1,
    borderColor: colors.border,
  },
  primaryButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.md,
    alignItems: 'center',
  },
  primaryButtonText: { color: colors.textInverse, fontWeight: '700' },
  smallButton: {
    backgroundColor: colors.primary,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.sm,
    alignItems: 'center',
  },
  smallButtonText: { color: colors.textInverse, fontWeight: '700' },
  smallButtonSecondary: {
    backgroundColor: colors.surfaceAlt,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.sm,
    alignItems: 'center',
  },
  smallButtonSecondaryText: { color: colors.text, fontWeight: '700' },
  disabled: { opacity: 0.5 },
  tagPill: {
    backgroundColor: colors.surfaceAlt,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radius.pill,
    fontSize: fontSize.xs,
    color: colors.text,
    overflow: 'hidden',
  },
  codeCard: {
    marginTop: spacing.sm,
    padding: spacing.sm,
    borderRadius: radius.sm,
    backgroundColor: colors.bg,
    borderWidth: 1,
    borderColor: colors.border,
    gap: 4,
  },
  codeValue: { fontFamily: 'monospace', color: colors.text, fontSize: fontSize.sm },
  error: { color: colors.danger, backgroundColor: colors.dangerMuted, padding: spacing.xs, borderRadius: radius.sm },
});

export default SocialScreen;
