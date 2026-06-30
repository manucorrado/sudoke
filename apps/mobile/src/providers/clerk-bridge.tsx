/**
 * Clerk integration bridge (PRD §4, §23.6 — Auth).
 *
 * We treat Clerk as an *optional* identity provider: the app runs guest-first
 * when Clerk is not configured. When `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` is
 * set, this file mounts Clerk and bridges its active session token into our
 * existing bearer storage + `/me` hydration.
 *
 * This indirection lets us:
 *   - ship the dev-bearer-paste flow today without requiring Clerk keys, and
 *   - drop in real sign-in/sign-up UI when the key is provisioned by simply
 *     setting an env var — no other call sites change.
 *
 */

import { useEffect, type ReactNode } from 'react';
import { ClerkProvider, useAuth as useClerkAuth } from '@clerk/clerk-expo';
import * as SecureStore from 'expo-secure-store';
import { useAuth } from '@/providers/auth';

// Expo inlines `process.env.EXPO_PUBLIC_*` at bundle time. We type-narrow
// through `globalThis.process` so this file does not depend on `@types/node`.
interface ExpoProcessEnv {
  readonly EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY?: string;
}
interface GlobalWithProcess {
  readonly process?: { readonly env?: ExpoProcessEnv };
}

const env = (globalThis as GlobalWithProcess).process?.env ?? {};

export const CLERK_PUBLISHABLE_KEY: string | undefined = env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY;

export const isClerkConfigured = (): boolean =>
  typeof CLERK_PUBLISHABLE_KEY === 'string' && CLERK_PUBLISHABLE_KEY.length > 0;

interface ClerkBridgeProps {
  readonly children: ReactNode;
}

export function ClerkBridge({ children }: ClerkBridgeProps) {
  const publishableKey = CLERK_PUBLISHABLE_KEY;
  if (!publishableKey) {
    return <>{children}</>;
  }

  return (
    <ClerkProvider publishableKey={publishableKey} tokenCache={tokenCache}>
      {children}
    </ClerkProvider>
  );
}

export function ClerkTokenBridge({ children }: ClerkBridgeProps) {
  if (!isClerkConfigured()) {
    return <>{children}</>;
  }

  return <ConfiguredClerkTokenBridge>{children}</ConfiguredClerkTokenBridge>;
}

function ConfiguredClerkTokenBridge({ children }: ClerkBridgeProps) {
  const { isLoaded, isSignedIn, getToken } = useClerkAuth();
  const { bearer, setBearer, refreshMe, signOut } = useAuth();

  useEffect(() => {
    let cancelled = false;

    async function syncToken() {
      if (!isLoaded) return;
      if (!isSignedIn) {
        if (bearer) await signOut();
        return;
      }

      const token = await getToken();
      if (cancelled || !token || token === bearer) return;
      await setBearer(token);
      if (!cancelled) {
        await refreshMe();
      }
    }

    void syncToken();

    return () => {
      cancelled = true;
    };
  }, [bearer, getToken, isLoaded, isSignedIn, refreshMe, setBearer, signOut]);

  return <>{children}</>;
}

const tokenCache = {
  getToken: (key: string) => SecureStore.getItemAsync(key),
  saveToken: (key: string, token: string) => SecureStore.setItemAsync(key, token),
};
