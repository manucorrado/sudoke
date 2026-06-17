import { Stack } from "expo-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { queryClient } from "@/providers/query-client";
import { AuthProvider } from "@/providers/auth";

export function RootLayout() {
  return (
    <SafeAreaProvider>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <Stack screenOptions={{ headerShown: false }} />
          <StatusBar style="auto" />
        </QueryClientProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}

export default RootLayout;
