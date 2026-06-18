/**
 * Clerk integration bridge (PRD §4, §23.6 — Auth).
 *
 * We treat Clerk as an *optional* identity provider during Epic 2: the app
 * runs guest-first even when Clerk is not configured. When the publishable
 * key is set via `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` we lazy-load
 * `@clerk/clerk-expo` and wire its session token into our `AuthProvider`
 * (which already owns bearer storage + `/me` hydration).
 *
 * This indirection lets us:
 *   - ship the dev-bearer-paste flow today without requiring Clerk keys, and
 *   - drop in real sign-in/sign-up UI when the key is provisioned by simply
 *     setting an env var — no other call sites change.
 *
 * Once Clerk keys are wired in CI/staging this module is where the
 * `<ClerkProvider tokenCache={...} publishableKey={...}>` mount and the
 * `useAuth().getToken()` → `setBearer()` bridge will live.
 */

import type { ReactNode } from 'react';

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

/**
 * Renders children directly today. When Clerk keys are configured this
 * component will mount `<ClerkProvider>` and a token bridge effect that
 * forwards Clerk's session JWT to our `AuthProvider.setBearer`.
 */
export function ClerkBridge({ children }: ClerkBridgeProps) {
  return <>{children}</>;
}
