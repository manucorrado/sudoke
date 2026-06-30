import { useMutation, useQueryClient } from '@tanstack/react-query';
import { sdk, type AuthContext, type ChallengeAcceptanceDTO } from '@/lib/sdk';
import { useAuth } from '@/providers/auth';

export function useRecordChallengeResult() {
  const { authCtx } = useAuth();
  const queryClient = useQueryClient();
  return useMutation<
    ChallengeAcceptanceDTO,
    Error,
    { readonly challengeId: string; readonly authCtx?: AuthContext }
  >({
    mutationFn: ({ challengeId, authCtx: overrideAuthCtx }) =>
      sdk.recordChallengeResult(challengeId, overrideAuthCtx ?? authCtx),
    onSuccess: (acceptance) => {
      void queryClient.invalidateQueries({
        queryKey: ['challenges', acceptance.challenge_id],
      });
      void queryClient.invalidateQueries({ queryKey: ['me', 'challenges'] });
    },
  });
}
