import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  sdk,
  type ChallengeDTO,
  type ChallengeDetailDTO,
  type FriendRequestListDTO,
  type FriendsListDTO,
  type MyChallengesDTO,
  type UserSearchResponseDTO,
} from '@/lib/sdk';
import { useAuth } from '@/providers/auth';

export function useFriends() {
  const { authCtx, status } = useAuth();
  return useQuery<FriendsListDTO>({
    queryKey: ['me', 'friends'],
    enabled: status === 'authenticated',
    queryFn: () => sdk.listFriends(authCtx),
    staleTime: 30_000,
  });
}

export function useFriendRequests() {
  const { authCtx, status } = useAuth();
  return useQuery<FriendRequestListDTO>({
    queryKey: ['me', 'friend-requests'],
    enabled: status === 'authenticated',
    queryFn: () => sdk.listFriendRequests(authCtx),
    staleTime: 15_000,
  });
}

export function useSearchUsers(query: string) {
  const { authCtx, status } = useAuth();
  return useQuery<UserSearchResponseDTO>({
    queryKey: ['users', 'search', query],
    enabled: status === 'authenticated' && query.trim().length > 0,
    queryFn: () => sdk.searchUsers(query, authCtx),
    staleTime: 10_000,
  });
}

export function useFriendActions() {
  const { authCtx } = useAuth();
  const qc = useQueryClient();
  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ['me', 'friends'] });
    void qc.invalidateQueries({ queryKey: ['me', 'friend-requests'] });
    void qc.invalidateQueries({ queryKey: ['users', 'search'] });
  };
  return {
    send: useMutation({
      mutationFn: (username: string) =>
        sdk.sendFriendRequest({ username }, authCtx),
      onSuccess: invalidate,
    }),
    accept: useMutation({
      mutationFn: (requestId: string) =>
        sdk.acceptFriendRequest(requestId, authCtx),
      onSuccess: invalidate,
    }),
    decline: useMutation({
      mutationFn: (requestId: string) =>
        sdk.declineFriendRequest(requestId, authCtx),
      onSuccess: invalidate,
    }),
    cancel: useMutation({
      mutationFn: (requestId: string) =>
        sdk.cancelFriendRequest(requestId, authCtx),
      onSuccess: invalidate,
    }),
  };
}

export function useMyChallenges() {
  const { authCtx, status } = useAuth();
  return useQuery<MyChallengesDTO>({
    queryKey: ['me', 'challenges'],
    enabled: status === 'authenticated',
    queryFn: () => sdk.listMyChallenges(authCtx),
    staleTime: 30_000,
  });
}

export function useCreateChallenge() {
  const { authCtx } = useAuth();
  const qc = useQueryClient();
  return useMutation<ChallengeDTO, Error, { daily_puzzle_id?: string } | undefined>({
    mutationFn: (payload) => sdk.createChallenge(payload, authCtx),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['me', 'challenges'] });
    },
  });
}

export function useResolveChallenge(code: string | null) {
  const { authCtx } = useAuth();
  return useQuery<ChallengeDetailDTO>({
    queryKey: ['challenges', 'by-code', code],
    enabled: code !== null && code.trim().length > 0,
    queryFn: () => sdk.resolveChallengeByCode(code!, authCtx),
    staleTime: 30_000,
  });
}

export function useChallengeDetail(challengeId: string, enabled = true) {
  const { authCtx } = useAuth();
  return useQuery<ChallengeDetailDTO>({
    queryKey: ['challenges', challengeId],
    enabled: enabled && challengeId.trim().length > 0,
    queryFn: () => sdk.getChallenge(challengeId, authCtx),
    staleTime: 30_000,
  });
}
