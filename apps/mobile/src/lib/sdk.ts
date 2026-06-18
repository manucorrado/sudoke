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
};
