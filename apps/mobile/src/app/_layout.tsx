import { Stack } from 'expo-router';
import { QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { queryClient } from '@/providers/query-client';
import { AuthProvider } from '@/providers/auth';
import { ClerkBridge, ClerkTokenBridge } from '@/providers/clerk-bridge';

/**
 * Root layout.
 *
 * Provider order (outermost first):
 *   SafeArea → ClerkBridge (optional Clerk SDK) → Auth → Clerk token bridge
 *   → ReactQuery → Router.
 *
 * The router is a `Stack` containing a single `(tabs)` group plus modal-like
 * routes (`onboarding`, `sign-in`, `c/[code]`). Auth/onboarding gating is
 * handled per-route, not globally, so deep links land on their intended
 * screen without an unnecessary redirect dance.
 */
export function RootLayout() {
  return (
    <SafeAreaProvider>
      <ClerkBridge>
        <AuthProvider>
          <ClerkTokenBridge>
            <QueryClientProvider client={queryClient}>
              <Stack screenOptions={{ headerShown: false }}>
                <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
                <Stack.Screen
                  name="onboarding"
                  options={{ presentation: 'modal', gestureEnabled: false }}
                />
                <Stack.Screen name="sign-in" options={{ presentation: 'modal' }} />
                <Stack.Screen name="c/[code]" options={{ presentation: 'modal' }} />
                <Stack.Screen name="dev" options={{ headerShown: true, title: 'Dev' }} />
              </Stack>
              <StatusBar style="auto" />
            </QueryClientProvider>
          </ClerkTokenBridge>
        </AuthProvider>
      </ClerkBridge>
    </SafeAreaProvider>
  );
}

export default RootLayout;
