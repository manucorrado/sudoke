import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  sdk,
  type NotificationPreferencesDTO,
  type StreakDTO,
} from '@/lib/sdk';
import { useAuth } from '@/providers/auth';

export function useStreak() {
  const { authCtx, status } = useAuth();
  return useQuery<StreakDTO>({
    queryKey: ['me', 'streak'],
    enabled: status === 'authenticated',
    queryFn: () => sdk.getMyStreak(authCtx),
    staleTime: 60_000,
  });
}

export function useNotificationPreferences() {
  const { authCtx, status } = useAuth();
  return useQuery<NotificationPreferencesDTO>({
    queryKey: ['me', 'notification-prefs'],
    enabled: status === 'authenticated',
    queryFn: () => sdk.getNotificationPreferences(authCtx),
    staleTime: 60_000,
  });
}

export function useUpdateNotificationPreferences() {
  const { authCtx } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<NotificationPreferencesDTO>) =>
      sdk.updateNotificationPreferences(payload, authCtx),
    onSuccess: (data) => {
      qc.setQueryData(['me', 'notification-prefs'], data);
    },
  });
}
