import { useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  clearPendingChallenge,
  getPendingChallenge,
  type PendingChallenge,
} from '@/features/social/pendingChallenge';
import { sdk, type ChallengeDetailDTO } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';

const pendingChallengeKey = ['pending-challenge'] as const;

export function usePendingChallenge(enabled: boolean) {
  const { authCtx } = useAuth();
  const queryClient = useQueryClient();
  const pending = useQuery<PendingChallenge>({
    queryKey: pendingChallengeKey,
    enabled,
    queryFn: getPendingChallenge,
    staleTime: 0,
  });
  const code = pending.data?.code?.trim() || null;
  const detail = useQuery<ChallengeDetailDTO>({
    queryKey: ['challenges', 'pending', code],
    enabled: enabled && code !== null,
    queryFn: () => sdk.resolveChallengeByCode(code ?? '', authCtx),
    staleTime: 30_000,
  });

  const clear = useCallback(async () => {
    await clearPendingChallenge();
    queryClient.setQueryData<PendingChallenge>(pendingChallengeKey, {
      code: null,
      challengeId: null,
    });
  }, [queryClient]);

  const matchesDaily = useCallback(
    (dailyId: string) => detail.data?.challenge.daily_puzzle_id === dailyId,
    [detail.data?.challenge.daily_puzzle_id],
  );

  return {
    code,
    challengeId: pending.data?.challengeId ?? detail.data?.challenge.id ?? null,
    detail: detail.data ?? null,
    isLoading: pending.isLoading || detail.isLoading,
    error: pending.error ?? detail.error,
    refetch: detail.refetch,
    clear,
    matchesDaily,
  };
}
