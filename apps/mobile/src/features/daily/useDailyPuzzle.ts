import { useQuery } from '@tanstack/react-query';
import { sdk, type DailyPuzzleDTO } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';

export const DAILY_QUERY_KEY = ['daily', 'current'] as const;

export function useDailyPuzzle() {
  const { authCtx, status } = useAuth();
  return useQuery<DailyPuzzleDTO>({
    queryKey: DAILY_QUERY_KEY,
    queryFn: () => sdk.getCurrentDaily(authCtx),
    enabled: status !== 'loading',
    staleTime: 60_000,
    retry: 1,
  });
}
