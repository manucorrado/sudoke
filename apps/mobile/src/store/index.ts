import { create } from "zustand";

type Theme = "light" | "dark" | "system";

interface AppState {
  theme: Theme;
  isGuest: boolean;
  setTheme: (theme: Theme) => void;
  setIsGuest: (isGuest: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: "system",
  isGuest: true,
  setTheme: (theme) => set({ theme }),
  setIsGuest: (isGuest) => set({ isGuest }),
}));
