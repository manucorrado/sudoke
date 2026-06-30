import { appStorage, StorageKeys } from '@/lib/storage';
import type { ChallengeDetailDTO } from '@/lib/sdk';

export interface PendingChallenge {
  readonly code: string | null;
  readonly challengeId: string | null;
}

export async function getPendingChallenge(): Promise<PendingChallenge> {
  const [code, challengeId] = await Promise.all([
    appStorage.get(StorageKeys.pendingChallengeCode),
    appStorage.get(StorageKeys.pendingChallengeId),
  ]);
  return { code, challengeId };
}

export async function setPendingChallenge(
  code: string,
  detail?: ChallengeDetailDTO,
): Promise<void> {
  await appStorage.set(StorageKeys.pendingChallengeCode, code);
  if (detail) {
    await appStorage.set(StorageKeys.pendingChallengeId, detail.challenge.id);
  }
}

export async function clearPendingChallenge(): Promise<void> {
  await Promise.all([
    appStorage.remove(StorageKeys.pendingChallengeCode),
    appStorage.remove(StorageKeys.pendingChallengeId),
  ]);
}
