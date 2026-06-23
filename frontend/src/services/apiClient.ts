import axios, {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from "axios";

const BASE_URL =
  (import.meta as any).env?.VITE_API_URL || "https://aiu-ny7v.onrender.com";

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

/* ─────────────────────────────────────────────
   REQUEST INTERCEPTOR (attach token)
───────────────────────────────────────────── */
apiClient.interceptors.request.use(
  async (config) => {
    config.headers.set("X-Request-ID", crypto.randomUUID());

    const raw = localStorage.getItem("aiu-auth");
    let token: string | null = null;

    if (raw) {
      try {
        token = JSON.parse(raw)?.state?.accessToken;
      } catch (e) {
        console.error("Auth parse error", e);
      }
    }

    if (token) {
      config.headers.set("Authorization", `Bearer ${token}`);
    }

    return config;
  },
  (error) => Promise.reject(error)
);

/* ─────────────────────────────────────────────
   REFRESH TOKEN HANDLING
───────────────────────────────────────────── */
let isRefreshing = false;
let refreshQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const isAuthRoute = (url?: string) => {
  if (!url) return false;

  return [
    "/auth/login/",
    "/auth/register/",
    "/auth/logout/",
    "/auth/token/refresh/",
  ].some((path) => url.includes(path));
};

const processQueue = (error: unknown, token: string | null = null) => {
  refreshQueue.forEach((request) => {
    if (error) {
      request.reject(error);
      return;
    }
    if (token) {
      request.resolve(token);
    }
  });
  refreshQueue = [];
};

/* ─────────────────────────────────────────────
   RESPONSE INTERCEPTOR
───────────────────────────────────────────── */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    if (
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !isAuthRoute(original.url)
    ) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          refreshQueue.push({ resolve, reject });
        }).then((token) => {
          original.headers.set("Authorization", `Bearer ${token}`);
          return apiClient(original);
        });
      }

      original._retry = true;
      isRefreshing = true;

      try {
        const { useAuthStore } = await import("../store/authStore");
        const refreshed =
          await useAuthStore.getState().refreshAccessToken();

        if (refreshed) {
          const newToken = useAuthStore.getState().accessToken;

          if (newToken) {
            processQueue(null, newToken);
            original.headers.set("Authorization", `Bearer ${newToken}`);
            return apiClient(original);
          }
        }

        processQueue(error);
        return Promise.reject(normalizeError(error));
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(normalizeError(error));
  }
);

/* ─────────────────────────────────────────────
   ERROR NORMALIZER
───────────────────────────────────────────── */
export interface APIError {
  message: string;
  code: number;
  errors: Record<string, string[]> | null;
  requestId?: string;
}

function extractMessage(value: unknown): string | null {
  if (typeof value === "string") {
    return value;
  }

  if (Array.isArray(value)) {
    const parts = value
      .map((item) => extractMessage(item))
      .filter((item): item is string => Boolean(item));
    return parts.length ? parts.join(" ") : null;
  }

  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;

    if ("detail" in record) {
      return extractMessage(record.detail);
    }

    if ("message" in record) {
      return extractMessage(record.message);
    }

    const parts = Object.entries(record)
      .flatMap(([key, nested]) => {
        const message = extractMessage(nested);
        return message ? [`${key}: ${message}`] : [];
      });

    return parts.length ? parts.join(" ") : null;
  }

  return null;
}

function normalizeError(error: AxiosError): APIError {
  const data = error.response?.data as
    | {
        error?: {
          message?: unknown;
          status_code?: number;
        };
        message?: string;
        detail?: string | string[];
        errors?: Record<string, string[]>;
        request_id?: string;
      }
    | undefined;

  const message =
    extractMessage(data?.error?.message) ||
    extractMessage(data?.message) ||
    extractMessage(data?.detail) ||
    error.message ||
    "An error occurred.";

  return {
    message,
    code: error.response?.status || 0,
    errors: data?.errors || null,
    requestId: data?.request_id,
  };
}

/* ─────────────────────────────────────────────
   HELPERS
───────────────────────────────────────────── */
const withQuery = (path: string, params: Record<string, string | undefined>) => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      searchParams.set(key, value);
    }
  });

  const query = searchParams.toString();
  return query ? `${path}?${query}` : path;
};

/* ─────────────────────────────────────────────
   API METHODS
───────────────────────────────────────────── */
export const api = {
  /* AUTH */
  login: (email: string, password: string) =>
    apiClient.post("/auth/login/", { email, password }),

  register: (data: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    timezone?: string;
    goals?: string[];
  }) => apiClient.post("/auth/register/", data),

  logout: (refresh: string) =>
    apiClient.post("/auth/logout/", { refresh }),

  refreshToken: (refresh: string) =>
    apiClient.post("/auth/token/refresh/", { refresh }),

  /* USER */
  getMe: () => apiClient.get("/users/me/"),

  updateMe: (data: Record<string, unknown>) =>
    apiClient.patch("/users/me/", data),

  changePassword: (data: {
    old_password: string;
    new_password: string;
  }) => apiClient.post("/users/change-password/", data),

  /* AI CHAT */
  sendMessage: (data: {
    message: string;
    conversation_id?: string;
    coach_mode?: string;
    context?: object;
  }) => apiClient.post("/ai/chat/", data),

  listConversations: () => apiClient.get("/ai/conversations/"),

  getConversation: (id: string) =>
    apiClient.get(`/ai/conversations/${id}/`),

  deleteConversation: (id: string) =>
    apiClient.delete(`/ai/conversations/${id}/`),

  /* HABITS */
  listHabits: () => apiClient.get("/habits/"),

  createHabit: (data: object) =>
    apiClient.post("/habits/", data),

  updateHabit: (id: string, data: object) =>
    apiClient.patch(`/habits/${id}/`, data),

  deleteHabit: (id: string) =>
    apiClient.delete(`/habits/${id}/`),

  logHabit: (id: string, data: object) =>
    apiClient.post(`/habits/${id}/log/`, data),

  getTodayHabits: () => apiClient.get("/habits/today/"),

  getHabitHistory: (id: string, days = 30) =>
    apiClient.get(
      withQuery(`/habits/${id}/history/`, { days: String(days) })
    ),

  /* ANALYTICS */
  getDashboardStats: () => apiClient.get("/analytics/dashboard/"),

  getBehaviorTimeline: (days = 7) =>
    apiClient.get(
      withQuery("/analytics/behavior/", { days: String(days) })
    ),

  getNudges: () => apiClient.get("/analytics/nudges/"),

  getInsights: (type?: string) =>
    apiClient.get(withQuery("/memory/insights/", { type })),

  /* RECOMMENDATIONS */
  listRecommendations: (status?: string) =>
    apiClient.get(withQuery("/recommendations/", { status })),

  acceptRecommendation: (id: string) =>
    apiClient.patch(`/recommendations/${id}/accept/`),

  dismissRecommendation: (id: string) =>
    apiClient.patch(`/recommendations/${id}/dismiss/`),

  /* GOALS */
  listGoals: (status?: string) =>
    apiClient.get(withQuery("/goals/", { status })),

  getGoal: (id: string) =>
    apiClient.get(`/goals/${id}/`),

  createGoal: (data: object) =>
    apiClient.post("/goals/", data),

  updateGoal: (id: string, data: object) =>
    apiClient.patch(`/goals/${id}/`, data),

  deleteGoal: (id: string) =>
    apiClient.delete(`/goals/${id}/`),

  activeGoals: () => apiClient.get("/goals/active/"),

  addMilestone: (goalId: string, data: object) =>
    apiClient.post(`/goals/${goalId}/add-milestone/`, data),

  completeMilestone: (goalId: string, milestoneId: string) =>
    apiClient.post(
      `/goals/${goalId}/milestones/${milestoneId}/complete/`,
      {}
    ),

  addGoalTask: (goalId: string, data: object) =>
    apiClient.post(`/goals/${goalId}/add-task/`, data),

  completeGoalTask: (goalId: string, taskId: string) =>
    apiClient.post(
      `/goals/${goalId}/tasks/${taskId}/complete/`,
      {}
    ),

  getGoalActivity: (goalId: string) =>
    apiClient.get(`/goals/${goalId}/activity/`),

  getGoalAiAdvice: (goalId: string) =>
    apiClient.post(`/goals/${goalId}/ai-advice/`, {}),

  completeGoal: (goalId: string) =>
    apiClient.post(`/goals/${goalId}/complete/`, {}),
};