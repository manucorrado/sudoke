import type { ReactNode } from "react";

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * TODO: Replace with real ClerkProvider once publishable key is configured.
 * Install @clerk/clerk-expo and wrap children with:
 *   <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
 *     {children}
 *   </ClerkProvider>
 */
export function AuthProvider({ children }: AuthProviderProps) {
  return <>{children}</>;
}
