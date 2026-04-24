// ─────────────────────────────────────────────────────────────────────────────
//  AIU — Auth Store (Zustand)
//  Manages auth state, tokens, and user profile in memory.
//  Tokens stored in memory only (access) + httpOnly cookie pattern recommended
//  for production — here using localStorage for simplicity with refresh logic.
// ─────────────────────────────────────────────────────────────────────────────

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { apiClient } from "../services/apiClient";

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  profile: {
    coach_mode: string;
    timezone: string;
    goals: string[];
    behavior_patterns: Record<string, any>;
    productivity_windows: number[];
    onboarding_completed: boolean;
  } | null;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
  updateUser: (user: Partial<User>) => void;
  setTokens: (access: string, refresh: string) => void;
}

interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  timezone?: string;
  goals?: string[];
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setTokens: (access, refresh) => {
        set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
        apiClient.defaults.headers.common["Authorization"] = `Bearer ${access}`;
      },

      login: async (email, password) => {
        const { data } = await apiClient.post("/auth/login/", { email, password });
        const { access, refresh } = data;
        get().setTokens(access, refresh);

        // Fetch full user profile
        const meResp = await apiClient.get("/users/me/");
        set({ user: meResp.data.data });
      },

      register: async (registerData) => {
        const { data } = await apiClient.post("/auth/register/", registerData);
        const { tokens, user } = data;
        get().setTokens(tokens.access, tokens.refresh);
        set({ user });
      },

      logout: async () => {
        const { refreshToken } = get();
        try {
          if (refreshToken) {
            await apiClient.post("/auth/logout/", { refresh: refreshToken });
          }
        } catch {
          // Swallow logout errors
        } finally {
          delete apiClient.defaults.headers.common["Authorization"];
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
          });
        }
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get();
        if (!refreshToken) return false;
        try {
          const { data } = await apiClient.post("/auth/token/refresh/", {
            refresh: refreshToken,
          });
          get().setTokens(data.access, refreshToken);
          return true;
        } catch {
          // Refresh failed — force logout
          get().logout();
          return false;
        }
      },

      updateUser: (updates) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        }));
      },
    }),
    {
      name: "aiu-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        // Re-attach token header after hydration
        if (state?.accessToken) {
          apiClient.defaults.headers.common["Authorization"] =
            `Bearer ${state.accessToken}`;
        }
      },
    }
  )
);
