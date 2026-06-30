/**
 * High-level Sudoke API client.
 *
 * Wraps the low-level `api` fetch wrapper with typed helpers and threads
 * the guest token from the auth context through every request.
 */

import { api } from './api';

export type AttemptStatus =
  | 'not_started'
  | 'previewing'
  | 'started'
  | 'in_progress'
  | 'submitted'
  | 'validated'
  | 'provisional_ranked'
  | 'finalized'
  | 'abandoned'
  | 'timed_out'
  | 'invalid'
  | 'under_review'
  | 'voided';

export interface DailyPuzzleDTO {
  readonly id: string;
  readonly scheduled_for: string;
  readonly activate_at: string;
  readonly finalize_at: string;
  readonly difficulty: 'easy' | 'medium' | 'hard' | 'expert';
  readonly estimated_min_seconds: number;
  readonly estimated_max_seconds: number;
  readonly givens: string;
}

export interface AttemptDTO {
  readonly id: string;
  readonly daily_puzzle_id: string;
  readonly status: AttemptStatus;
  readonly previewed_at: string | null;
  readonly started_at: string | null;
  readonly submitted_at: string | null;
  readonly abandoned_at: string | null;
  readonly mistakes: number;
  readonly official_duration_ms: number | null;
  readonly under_review_reason: string | null;
}

export interface GuestSessionDTO {
  readonly id: string;
  readonly token: string;
  readonly created_at: string;
}

export interface MeDTO {
  readonly id: string;
  readonly username: string | null;
  readonly display_name: string | null;
  readonly avatar_url: string | null;
  readonly role: 'player' | 'admin';
  readonly is_guest: boolean;
  readonly email: string | null;
  readonly created_at: string;
}

export type RatingTier =
  | 'bronze'
  | 'silver'
  | 'gold'
  | 'platinum'
  | 'diamond'
  | 'master';

export interface RatingDTO {
  readonly rating: number;
  readonly tier: RatingTier;
  readonly provisional_completions: number;
  readonly is_provisional: boolean;
  readonly calculation_version: string;
  readonly last_updated_at: string | null;
}

export interface RatingHistoryEntryDTO {
  readonly daily_puzzle_id: string;
  readonly attempt_id: string;
  readonly kind: 'projected' | 'final';
  readonly old_rating: number;
  readonly new_rating: number;
  readonly delta: number;
  readonly percentile: number | null;
  readonly cohort_size: number;
  readonly was_provisional: boolean;
  readonly calculation_version: string;
  readonly applied_at: string;
}

export interface RatingHistoryDTO {
  readonly entries: readonly RatingHistoryEntryDTO[];
}

export type LeaderboardView = 'global' | 'nearby' | 'friends' | 'historical';

export interface LeaderboardRowDTO {
  readonly rank: number;
  readonly user_id: string;
  readonly username: string | null;
  readonly display_name: string | null;
  readonly avatar_url: string | null;
  readonly official_duration_ms: number;
  readonly mistakes: number;
  readonly rating: number;
  readonly rating_delta: number | null;
  readonly tier: RatingTier;
  readonly is_me: boolean;
}

export interface LeaderboardDTO {
  readonly daily_puzzle_id: string;
  readonly view: LeaderboardView;
  readonly cohort_size: number;
  readonly is_final: boolean;
  readonly rows: readonly LeaderboardRowDTO[];
}

export interface MyResultDTO {
  readonly daily_puzzle_id: string;
  readonly attempt_id: string;
  readonly status: AttemptStatus;
  readonly rank: number | null;
  readonly cohort_size: number;
  readonly percentile: number | null;
  readonly mistakes: number;
  readonly official_duration_ms: number | null;
  readonly rating_before: number | null;
  readonly rating_after: number | null;
  readonly rating_delta: number | null;
  readonly was_provisional: boolean;
  readonly tier: RatingTier | null;
  readonly is_final: boolean;
}

export interface AuthContext {
  readonly bearer?: string;
  readonly guestToken?: string;
}

export interface GuestClaimContext {
  readonly bearer: string;
  readonly guestToken: string;
}

function headersFor(ctx: AuthContext): Record<string, string> {
  const headers: Record<string, string> = {};
  if (ctx.bearer) headers.Authorization = `Bearer ${ctx.bearer}`;
  if (ctx.guestToken) headers['X-Guest-Token'] = ctx.guestToken;
  return headers;
}

export const sdk = {
  async createGuestSession(opts: { locale?: string } = {}): Promise<GuestSessionDTO> {
    return api.post<GuestSessionDTO>('/guest/sessions', { locale: opts.locale ?? null });
  },

  async getCurrentDaily(ctx: AuthContext): Promise<DailyPuzzleDTO> {
    return api.get<DailyPuzzleDTO>('/daily/current', { headers: headersFor(ctx) });
  },

  async previewDaily(dailyId: string, ctx: AuthContext): Promise<AttemptDTO> {
    return api.post<AttemptDTO>(`/daily/${dailyId}/preview`, undefined, {
      headers: headersFor(ctx),
    });
  },

  async startDaily(dailyId: string, ctx: AuthContext): Promise<AttemptDTO> {
    return api.post<AttemptDTO>(`/daily/${dailyId}/start`, undefined, {
      headers: headersFor(ctx),
    });
  },

  async submitAttempt(
    attemptId: string,
    payload: { submitted_grid: string; mistakes: number },
    ctx: AuthContext,
  ): Promise<AttemptDTO> {
    return api.post<AttemptDTO>(`/ranked-attempts/${attemptId}/submit`, payload, {
      headers: headersFor(ctx),
    });
  },

  async abandonAttempt(attemptId: string, ctx: AuthContext): Promise<AttemptDTO> {
    return api.post<AttemptDTO>(`/ranked-attempts/${attemptId}/abandon`, undefined, {
      headers: headersFor(ctx),
    });
  },

  async getMe(ctx: AuthContext): Promise<MeDTO> {
    return api.get<MeDTO>('/me', { headers: headersFor(ctx) });
  },

  async claimGuest(ctx: GuestClaimContext): Promise<MeDTO> {
    return api.post<MeDTO>('/me/claim-guest', undefined, {
      headers: headersFor(ctx),
    });
  },

  async updateProfile(
    payload: { username?: string; display_name?: string; avatar_url?: string },
    ctx: AuthContext,
  ): Promise<MeDTO> {
    return api.patch<MeDTO>('/me/profile', payload, { headers: headersFor(ctx) });
  },

  async getMyRating(ctx: AuthContext): Promise<RatingDTO> {
    return api.get<RatingDTO>('/me/rating', { headers: headersFor(ctx) });
  },

  async getMyRatingHistory(
    ctx: AuthContext,
    opts: { limit?: number; kind?: 'projected' | 'final' } = {},
  ): Promise<RatingHistoryDTO> {
    const query = new URLSearchParams();
    if (opts.limit !== undefined) query.set('limit', String(opts.limit));
    if (opts.kind) query.set('kind', opts.kind);
    const qs = query.toString();
    return api.get<RatingHistoryDTO>(
      `/me/rating/history${qs ? `?${qs}` : ''}`,
      { headers: headersFor(ctx) },
    );
  },

  async getDailyLeaderboard(
    dailyId: string,
    ctx: AuthContext,
    opts: { view?: LeaderboardView; limit?: number } = {},
  ): Promise<LeaderboardDTO> {
    const query = new URLSearchParams();
    if (opts.view) query.set('view', opts.view);
    if (opts.limit !== undefined) query.set('limit', String(opts.limit));
    const qs = query.toString();
    return api.get<LeaderboardDTO>(
      `/daily/${dailyId}/leaderboard${qs ? `?${qs}` : ''}`,
      { headers: headersFor(ctx) },
    );
  },

  async getMyDailyResult(dailyId: string, ctx: AuthContext): Promise<MyResultDTO> {
    return api.get<MyResultDTO>(`/daily/${dailyId}/my-result`, {
      headers: headersFor(ctx),
    });
  },

  // ---- Epic 7: archive + ghost rank ----
  async getArchive(
    ctx: AuthContext,
    opts: { limit?: number; offset?: number } = {},
  ): Promise<ArchiveListDTO> {
    const q = new URLSearchParams();
    if (opts.limit !== undefined) q.set('limit', String(opts.limit));
    if (opts.offset !== undefined) q.set('offset', String(opts.offset));
    const qs = q.toString();
    return api.get<ArchiveListDTO>(`/archive${qs ? `?${qs}` : ''}`, {
      headers: headersFor(ctx),
    });
  },

  async getArchiveDetail(
    dailyId: string,
    ctx: AuthContext,
  ): Promise<ArchiveDetailDTO> {
    return api.get<ArchiveDetailDTO>(`/archive/${dailyId}`, {
      headers: headersFor(ctx),
    });
  },

  async getUpcoming(
    ctx: AuthContext,
    opts: { limit?: number } = {},
  ): Promise<UpcomingListDTO> {
    const q = new URLSearchParams();
    if (opts.limit !== undefined) q.set('limit', String(opts.limit));
    const qs = q.toString();
    return api.get<UpcomingListDTO>(`/archive/upcoming${qs ? `?${qs}` : ''}`, {
      headers: headersFor(ctx),
    });
  },

  async getGhostRank(
    dailyId: string,
    payload: { duration_ms: number; mistakes: number },
    ctx: AuthContext,
  ): Promise<GhostRankDTO> {
    return api.post<GhostRankDTO>(`/archive/${dailyId}/ghost-rank`, payload, {
      headers: headersFor(ctx),
    });
  },

  async getArchiveMyResult(
    dailyId: string,
    ctx: AuthContext,
  ): Promise<ArchiveMyResultDTO> {
    return api.get<ArchiveMyResultDTO>(`/archive/${dailyId}/my-result`, {
      headers: headersFor(ctx),
    });
  },

  // ---- Epic 8: streak + notification preferences ----
  async getMyStreak(ctx: AuthContext): Promise<StreakDTO> {
    return api.get<StreakDTO>('/me/streak', { headers: headersFor(ctx) });
  },

  async registerPushToken(
    payload: { token: string; platform: PushPlatform },
    ctx: AuthContext,
  ): Promise<PushTokenDTO> {
    return api.post<PushTokenDTO>('/me/push-tokens', payload, {
      headers: headersFor(ctx),
    });
  },

  async unregisterPushToken(token: string, ctx: AuthContext): Promise<void> {
    return api.delete<void>(
      `/me/push-tokens?token=${encodeURIComponent(token)}`,
      { headers: headersFor(ctx) },
    );
  },

  async getNotificationPreferences(
    ctx: AuthContext,
  ): Promise<NotificationPreferencesDTO> {
    return api.get<NotificationPreferencesDTO>(
      '/me/notifications/preferences',
      { headers: headersFor(ctx) },
    );
  },

  async updateNotificationPreferences(
    payload: Partial<NotificationPreferencesDTO>,
    ctx: AuthContext,
  ): Promise<NotificationPreferencesDTO> {
    return api.patch<NotificationPreferencesDTO>(
      '/me/notifications/preferences',
      payload,
      { headers: headersFor(ctx) },
    );
  },

  // ---- Epic 6: friends + challenges ----
  async listFriends(ctx: AuthContext): Promise<FriendsListDTO> {
    return api.get<FriendsListDTO>('/me/friends', { headers: headersFor(ctx) });
  },

  async listFriendRequests(ctx: AuthContext): Promise<FriendRequestListDTO> {
    return api.get<FriendRequestListDTO>('/me/friends/requests', {
      headers: headersFor(ctx),
    });
  },

  async sendFriendRequest(
    payload: { username: string },
    ctx: AuthContext,
  ): Promise<FriendRequestDTO> {
    return api.post<FriendRequestDTO>('/me/friends/requests', payload, {
      headers: headersFor(ctx),
    });
  },

  async acceptFriendRequest(
    requestId: string,
    ctx: AuthContext,
  ): Promise<FriendRequestDTO> {
    return api.post<FriendRequestDTO>(
      `/me/friends/requests/${requestId}/accept`,
      undefined,
      { headers: headersFor(ctx) },
    );
  },

  async declineFriendRequest(
    requestId: string,
    ctx: AuthContext,
  ): Promise<FriendRequestDTO> {
    return api.post<FriendRequestDTO>(
      `/me/friends/requests/${requestId}/decline`,
      undefined,
      { headers: headersFor(ctx) },
    );
  },

  async cancelFriendRequest(
    requestId: string,
    ctx: AuthContext,
  ): Promise<FriendRequestDTO> {
    return api.delete<FriendRequestDTO>(
      `/me/friends/requests/${requestId}`,
      { headers: headersFor(ctx) },
    );
  },

  async searchUsers(
    query: string,
    ctx: AuthContext,
    opts: { limit?: number } = {},
  ): Promise<UserSearchResponseDTO> {
    const q = new URLSearchParams({ q: query });
    if (opts.limit !== undefined) q.set('limit', String(opts.limit));
    return api.get<UserSearchResponseDTO>(`/users/search?${q.toString()}`, {
      headers: headersFor(ctx),
    });
  },

  async createChallenge(
    payload: { daily_puzzle_id?: string } | undefined,
    ctx: AuthContext,
  ): Promise<ChallengeDTO> {
    return api.post<ChallengeDTO>('/me/challenges', payload ?? {}, {
      headers: headersFor(ctx),
    });
  },

  async listMyChallenges(ctx: AuthContext): Promise<MyChallengesDTO> {
    return api.get<MyChallengesDTO>('/me/challenges', {
      headers: headersFor(ctx),
    });
  },

  async resolveChallengeByCode(
    code: string,
    ctx: AuthContext,
  ): Promise<ChallengeDetailDTO> {
    return api.get<ChallengeDetailDTO>(`/challenges/by-code/${code}`, {
      headers: headersFor(ctx),
    });
  },

  async getChallenge(
    challengeId: string,
    ctx: AuthContext,
  ): Promise<ChallengeDetailDTO> {
    return api.get<ChallengeDetailDTO>(`/challenges/${challengeId}`, {
      headers: headersFor(ctx),
    });
  },

  async recordChallengeResult(
    challengeId: string,
    ctx: AuthContext,
  ): Promise<ChallengeAcceptanceDTO> {
    return api.post<ChallengeAcceptanceDTO>(
      `/challenges/${challengeId}/results`,
      undefined,
      { headers: headersFor(ctx) },
    );
  },
};

// ---- Epic 7 DTOs ----

export type Difficulty = 'easy' | 'medium' | 'hard' | 'expert';

export interface ArchiveEntryDTO {
  readonly daily_puzzle_id: string;
  readonly puzzle_id: string;
  readonly scheduled_for: string;
  readonly difficulty: Difficulty;
  readonly estimated_min_seconds: number;
  readonly estimated_max_seconds: number;
  readonly is_final: boolean;
}

export interface ArchiveListDTO {
  readonly entries: readonly ArchiveEntryDTO[];
}

export interface ArchiveDetailDTO {
  readonly daily_puzzle_id: string;
  readonly puzzle_id: string;
  readonly scheduled_for: string;
  readonly difficulty: Difficulty;
  readonly estimated_min_seconds: number;
  readonly estimated_max_seconds: number;
  readonly givens: string;
  readonly solution: string;
  readonly is_final: boolean;
}

export interface UpcomingEntryDTO {
  readonly scheduled_for: string;
  readonly difficulty: Difficulty;
}

export interface UpcomingListDTO {
  readonly entries: readonly UpcomingEntryDTO[];
}

export interface GhostRankDTO {
  readonly daily_puzzle_id: string;
  readonly duration_ms: number;
  readonly mistakes: number;
  readonly ghost_rank: number | null;
  readonly cohort_size: number;
  readonly percentile: number | null;
  readonly is_official: boolean;
}

export interface ArchiveMyResultDTO {
  readonly daily_puzzle_id: string;
  readonly played: boolean;
  readonly result: MyResultDTO | null;
}

// ---- Epic 8 DTOs ----

export interface StreakDTO {
  readonly current_length: number;
  readonly longest_length: number;
  readonly freezes_held: number;
  readonly max_freezes: number;
  readonly completions_total: number;
  readonly last_completed_date: string | null;
  readonly streak_started_date: string | null;
}

export interface NotificationPreferencesDTO {
  readonly daily_reminder: boolean;
  readonly friend_challenged_you: boolean;
  readonly beat_your_time: boolean;
  readonly final_ranking_ready: boolean;
}

export type PushPlatform = 'ios' | 'android' | 'web';

export interface PushTokenDTO {
  readonly token: string;
  readonly platform: string;
}

// ---- Epic 6 DTOs ----

export type FriendRelationship =
  | 'self'
  | 'friends'
  | 'request_sent'
  | 'request_received'
  | 'none';

export interface UserSearchResultDTO {
  readonly id: string;
  readonly username: string | null;
  readonly display_name: string | null;
  readonly avatar_url: string | null;
  readonly relationship: FriendRelationship;
}

export interface UserSearchResponseDTO {
  readonly results: readonly UserSearchResultDTO[];
}

export interface FriendDTO {
  readonly user_id: string;
  readonly username: string | null;
  readonly display_name: string | null;
  readonly avatar_url: string | null;
  readonly friend_since: string;
}

export interface FriendsListDTO {
  readonly friends: readonly FriendDTO[];
}

export interface FriendRequestDTO {
  readonly id: string;
  readonly from_user_id: string;
  readonly to_user_id: string;
  readonly from_username: string | null;
  readonly from_display_name: string | null;
  readonly to_username: string | null;
  readonly to_display_name: string | null;
  readonly status: string;
  readonly created_at: string;
  readonly responded_at: string | null;
}

export interface FriendRequestListDTO {
  readonly incoming: readonly FriendRequestDTO[];
  readonly outgoing: readonly FriendRequestDTO[];
}

export interface ChallengeDTO {
  readonly id: string;
  readonly code: string;
  readonly daily_puzzle_id: string;
  readonly challenger_user_id: string;
  readonly challenger_username: string | null;
  readonly challenger_display_name: string | null;
  readonly challenger_duration_ms: number | null;
  readonly challenger_mistakes: number | null;
  readonly status: string;
  readonly created_at: string;
  readonly expires_at: string | null;
  readonly share_url: string;
}

export interface ChallengeAcceptanceDTO {
  readonly id: string;
  readonly challenge_id: string;
  readonly recipient_user_id: string | null;
  readonly recipient_username: string | null;
  readonly recipient_display_name: string | null;
  readonly duration_ms: number | null;
  readonly mistakes: number | null;
  readonly completed_at: string | null;
}

export interface ChallengeDetailDTO {
  readonly challenge: ChallengeDTO;
  readonly acceptances: readonly ChallengeAcceptanceDTO[];
  readonly daily_difficulty: Difficulty;
  readonly daily_scheduled_for: string;
}

export interface MyChallengesDTO {
  readonly sent: readonly ChallengeDTO[];
  readonly received: readonly ChallengeDTO[];
}
