import { Platform } from "react-native";
import * as SecureStore from "expo-secure-store";
import AsyncStorage from "@react-native-async-storage/async-storage";

/**
 * Storage layer (PRD §23 — Mobile state).
 *
 * - `secureStorage` is backed by Expo SecureStore (Keychain / Keystore) and is
 *   reserved for credentials (bearer tokens, refresh tokens).
 * - `appStorage` is AsyncStorage for non-sensitive UI state such as the guest
 *   token, onboarding completion, and pending challenge codes.
 *
 * On web we transparently fall back to AsyncStorage for secure values because
 * SecureStore is not available — this only affects Expo Web devex (real
 * mobile builds always use the keychain).
 */

const isWeb = Platform.OS === "web";

export const secureStorage = {
  async get(key: string): Promise<string | null> {
    if (isWeb) return AsyncStorage.getItem(key);
    return SecureStore.getItemAsync(key);
  },

  async set(key: string, value: string): Promise<void> {
    if (isWeb) {
      await AsyncStorage.setItem(key, value);
      return;
    }
    await SecureStore.setItemAsync(key, value);
  },

  async remove(key: string): Promise<void> {
    if (isWeb) {
      await AsyncStorage.removeItem(key);
      return;
    }
    await SecureStore.deleteItemAsync(key);
  },
};

export const appStorage = {
  async get(key: string): Promise<string | null> {
    return AsyncStorage.getItem(key);
  },

  async set(key: string, value: string): Promise<void> {
    await AsyncStorage.setItem(key, value);
  },

  async remove(key: string): Promise<void> {
    await AsyncStorage.removeItem(key);
  },
};

export const StorageKeys = {
  guestToken: "sudoke:guest_token",
  bearer: "sudoke:auth_token",
  onboardingCompletedAt: "sudoke:onboarding_completed_at",
  pendingChallengeCode: "sudoke:pending_challenge_code",
  pendingChallengeId: "sudoke:pending_challenge_id",
  notificationPrefs: "sudoke:notification_prefs",
} as const;
