/**
 * Tracks first-launch onboarding completion (PRD §5).
 *
 * Onboarding is considered "completed" once the player has either:
 *   - chosen the guest path (tapped "Play a quick puzzle"), or
 *   - opened the sign-in screen at least once.
 *
 * The flag is stored in AsyncStorage so it survives reinstall-less restarts
 * but does NOT survive a fresh install — which is exactly the desired UX.
 */

import { useCallback, useEffect, useState } from 'react';
import { appStorage, StorageKeys } from '@/lib/storage';

type Status = 'loading' | 'pending' | 'completed';

export function useOnboarding() {
  const [status, setStatus] = useState<Status>('loading');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const raw = await appStorage.get(StorageKeys.onboardingCompletedAt);
      if (cancelled) return;
      setStatus(raw ? 'completed' : 'pending');
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const markCompleted = useCallback(async () => {
    await appStorage.set(StorageKeys.onboardingCompletedAt, new Date().toISOString());
    setStatus('completed');
  }, []);

  const reset = useCallback(async () => {
    await appStorage.remove(StorageKeys.onboardingCompletedAt);
    setStatus('pending');
  }, []);

  return { status, markCompleted, reset } as const;
}
