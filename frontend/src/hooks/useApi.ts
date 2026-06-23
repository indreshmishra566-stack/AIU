// ─────────────────────────────────────────────────────────────────────────────
//  AIU — Custom React Query Hooks
//  Centralised data fetching, mutations, and cache management.
// ─────────────────────────────────────────────────────────────────────────────

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { api } from "../services/apiClient";

// ── Query keys (constants prevent typos) ─────────────────────────────────────
export const QUERY_KEYS = {
  me:               ["me"] as const,
  conversations:    ["conversations"] as const,
  conversation:     (id: string) => ["conversation", id] as const,
  habits:           ["habits"] as const,
  habitsToday:      ["habits-today"] as const,
  habitHistory:     (id: string, days: number) => ["habit-history", id, days] as const,
  dashboardStats:   ["dashboard-stats"] as const,
  behaviorTimeline: (days: number) => ["behavior-timeline", days] as const,
  insights:         (type?: string) => ["insights", type ?? "all"] as const,
  recommendations:  (status?: string) => ["recommendations", status ?? "all"] as const,
};

// ── Auth / User ───────────────────────────────────────────────────────────────

export function useMe() {
  return useQuery({
    queryKey: QUERY_KEYS.me,
    queryFn: () => api.getMe().then((r) => r.data.data),
    staleTime: 1000 * 60 * 5,
  });
}

export function useUpdateMe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => api.updateMe(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.me });
      toast.success("Profile updated!");
    },
    onError: () => toast.error("Failed to update profile."),
  });
}

// ── Conversations ─────────────────────────────────────────────────────────────

export function useConversations() {
  return useQuery({
    queryKey: QUERY_KEYS.conversations,
    queryFn: () => api.listConversations().then((r) => r.data.results),
  });
}

export function useConversation(id: string | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.conversation(id!),
    queryFn: () => api.getConversation(id!).then((r) => r.data),
    enabled: !!id,
  });
}

export function useDeleteConversation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteConversation(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.conversations });
      toast.success("Conversation archived.");
    },
  });
}

// ── Habits ────────────────────────────────────────────────────────────────────

export function useHabits() {
  return useQuery({
    queryKey: QUERY_KEYS.habits,
    queryFn: () => api.listHabits().then((r) => r.data.results),
  });
}

export function useTodayHabits() {
  return useQuery({
    queryKey: QUERY_KEYS.habitsToday,
    queryFn: () => api.getTodayHabits().then((r) => r.data),
    refetchInterval: 1000 * 60,  // Re-fetch every minute
  });
}

export function useHabitHistory(id: string, days = 30) {
  return useQuery({
    queryKey: QUERY_KEYS.habitHistory(id, days),
    queryFn: () => api.getHabitHistory(id, days).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCreateHabit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => api.createHabit(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.habits });
      qc.invalidateQueries({ queryKey: QUERY_KEYS.habitsToday });
      toast.success("Habit created!");
    },
    onError: () => toast.error("Failed to create habit."),
  });
}

export function useDeleteHabit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteHabit(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.habits });
      qc.invalidateQueries({ queryKey: QUERY_KEYS.habitsToday });
      toast.success("Habit removed.");
    },
  });
}

export function useLogHabit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: Record<string, unknown> }) =>
      api.logHabit(id, data ?? {}),
    onMutate: async ({ id }) => {
      // Optimistic update
      await qc.cancelQueries({ queryKey: QUERY_KEYS.habitsToday });
      const prev = qc.getQueryData(QUERY_KEYS.habitsToday);
      qc.setQueryData(QUERY_KEYS.habitsToday, (old: any) => {
        if (!old?.results) return old;
        return {
          ...old,
          results: old.results.map((h: any) =>
            h.id === id
              ? { ...h, completed_today: true, current_streak: h.current_streak + 1 }
              : h
          ),
        };
      });
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.prev) qc.setQueryData(QUERY_KEYS.habitsToday, ctx.prev);
      toast.error("Failed to log habit.");
    },
    onSuccess: (res) => {
      const streak = res.data?.current_streak;
      toast.success(streak > 1 ? `🔥 ${streak} day streak!` : "Logged!");
      qc.invalidateQueries({ queryKey: QUERY_KEYS.habitsToday });
      qc.invalidateQueries({ queryKey: QUERY_KEYS.dashboardStats });
    },
  });
}

// ── Analytics ────────────────────────────────────────────────────────────────

export function useDashboardStats() {
  return useQuery({
    queryKey: QUERY_KEYS.dashboardStats,
    queryFn: () => api.getDashboardStats().then((r) => r.data.data),
    refetchInterval: 1000 * 60 * 5,
  });
}

export function useBehaviorTimeline(days = 7) {
  return useQuery({
    queryKey: QUERY_KEYS.behaviorTimeline(days),
    queryFn: () => api.getBehaviorTimeline(days).then((r) => r.data.events),
  });
}

// ── Insights ──────────────────────────────────────────────────────────────────

export function useInsights(type?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.insights(type),
    queryFn: () => api.getInsights(type).then((r) => r.data.results),
  });
}

// ── Recommendations ───────────────────────────────────────────────────────────

export function useRecommendations(status?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.recommendations(status),
    queryFn: () => api.listRecommendations(status).then((r) => r.data.results),
  });
}

export function useAcceptRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.acceptRecommendation(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.recommendations() });
      toast.success("Added to your plan!");
    },
  });
}

export function useDismissRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.dismissRecommendation(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.recommendations() });
    },
  });
}
