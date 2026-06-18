import { useQuery } from '@tanstack/react-query';
import {
  sdk,
  type LeaderboardDTO,
  type LeaderboardView,
  type MyResultDTO,
} from '@/lib/sdk';
import { useAuth } from '@/providers/auth';

export const leaderboardKey = (dailyId: string, view: LeaderboardView) =>
  ['leaderboard', dailyId, view] as const;

export function useDailyLeaderboard(
  dailyId: string | undefined,
  view: LeaderboardView,
  limit = 25,
) {
  const { authCtx } = useAuth();
  return useQuery<LeaderboardDTO>({
    queryKey: dailyId ? leaderboardKey(dailyId, view) : ['leaderboard', 'none'],
    queryFn: () => sdk.getDailyLeaderboard(dailyId!, authCtx, { view, limit }),
    enabled: Boolean(dailyId),
    staleTime: 15_000,
  });
}

export const myResultKey = (dailyId: string) =>
  ['my-result', dailyId] as const;

export function useMyDailyResult(dailyId: string | undefined) {
  const { authCtx, status } = useAuth();
  return useQuery<MyResultDTO>({
    queryKey: dailyId ? myResultKey(dailyId) : ['my-result', 'none'],
    queryFn: () => sdk.getMyDailyResult(dailyId!, authCtx),
    enabled: Boolean(dailyId) && status === 'authenticated',
    retry: false,
    staleTime: 30_000,
  });
}
