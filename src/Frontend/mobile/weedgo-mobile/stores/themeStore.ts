import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeState {
  mode: ThemeMode;
  isDark: boolean;
  setThemeMode: (mode: ThemeMode) => void;
  syncWithSystem: (isDarkSystem: boolean) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      isDark: false,

      setThemeMode: (mode: ThemeMode) => {
        const state = get();
        let isDark = state.isDark;

        if (mode === 'light') {
          isDark = false;
        } else if (mode === 'dark') {
          isDark = true;
        }
        // If system, isDark will be set by syncWithSystem

        set({ mode, isDark });
      },

      syncWithSystem: (isDarkSystem: boolean) => {
        const state = get();
        if (state.mode === 'system') {
          set({ isDark: isDarkSystem });
        }
      },
    }),
    {
      name: 'theme-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({ mode: state.mode }),
    }
  )
);