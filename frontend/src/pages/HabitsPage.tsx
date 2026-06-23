// ─────────────────────────────────────────────────────────────────────────────
//  AIU — Habits Page
//  Daily habit tracking with streaks, progress rings, and history.
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import {
  Plus, Flame, CheckCircle2, Circle, Trophy,
  ChevronRight, X, Target, Calendar,
} from "lucide-react";
import { api } from "../services/apiClient";
import { format } from "date-fns";
import clsx from "clsx";

interface Habit {
  id: string;
  name: string;
  description: string;
  category: string;
  frequency: string;
  current_streak: number;
  longest_streak: number;
  total_completions: number;
  is_active: boolean;
  completion_rate_7d: number;
  completed_today?: boolean;
}

const CATEGORIES = [
  "health", "productivity", "learning", "mindfulness", "social", "finance", "other"
];

export default function HabitsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [newHabit, setNewHabit] = useState({ name: "", category: "productivity", description: "" });

  const { data: habits, isLoading } = useQuery({
    queryKey: ["habits-today"],
    queryFn: () => api.getTodayHabits().then((r) => r.data.results as Habit[]),
    refetchInterval: 1000 * 60,
  });

  const logMutation = useMutation({
    mutationFn: ({ id }: { id: string }) =>
      api.logHabit(id, { log_date: format(new Date(), "yyyy-MM-dd") }),
    onMutate: async ({ id }) => {
      // Optimistic update
      await queryClient.cancelQueries({ queryKey: ["habits-today"] });
      const prev = queryClient.getQueryData(["habits-today"]);
      queryClient.setQueryData(["habits-today"], (old: any) => ({
        ...old,
        results: old?.results?.map((h: Habit) =>
          h.id === id
            ? { ...h, completed_today: true, current_streak: h.current_streak + 1 }
            : h
        ),
      }));
      return { prev };
    },
    onError: (_err, _vars, ctx) => {
      queryClient.setQueryData(["habits-today"], ctx?.prev);
      toast.error("Failed to log habit");
    },
    onSuccess: (data) => {
      toast.success(
        data.data.current_streak > 1
          ? `🔥 ${data.data.current_streak} day streak!`
          : "Habit logged!"
      );
      queryClient.invalidateQueries({ queryKey: ["habits-today"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: typeof newHabit) => api.createHabit(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["habits-today"] });
      setShowForm(false);
      setNewHabit({ name: "", category: "productivity", description: "" });
      toast.success("Habit created!");
    },
    onError: () => toast.error("Failed to create habit"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteHabit(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["habits-today"] });
      toast.success("Habit removed");
    },
  });

  const completedCount = habits?.filter((h) => h.completed_today).length ?? 0;
  const totalCount = habits?.length ?? 0;
  const completionPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Habits</h1>
          <p className="text-sm text-gray-500 mt-1">
            {format(new Date(), "EEEE, MMMM d")} · {completedCount}/{totalCount} complete
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium
                     bg-violet-600 hover:bg-violet-700 text-white transition-colors"
        >
          <Plus size={16} /> Add habit
        </button>
      </div>

      {/* ── Progress Ring ──────────────────────────────────────────────────── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200
                      dark:border-gray-800 p-6 flex items-center gap-6">
        <ProgressRing pct={completionPct} />
        <div>
          <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            {completionPct}%
          </p>
          <p className="text-sm text-gray-500">today's completion</p>
          <div className="flex items-center gap-4 mt-3">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 size={14} className="text-green-500" />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {completedCount} done
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Circle size={14} className="text-gray-300" />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {totalCount - completedCount} remaining
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Habit List ─────────────────────────────────────────────────────── */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
          ))}
        </div>
      ) : habits?.length === 0 ? (
        <EmptyHabits onAdd={() => setShowForm(true)} />
      ) : (
        <div className="space-y-3">
          {habits?.map((habit) => (
            <HabitCard
              key={habit.id}
              habit={habit}
              onLog={() => logMutation.mutate({ id: habit.id })}
              onDelete={() => deleteMutation.mutate(habit.id)}
              isLogging={logMutation.isPending}
            />
          ))}
        </div>
      )}

      {/* ── Add Habit Modal ────────────────────────────────────────────────── */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center
                        z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 w-full max-w-md
                          border border-gray-200 dark:border-gray-800 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">New habit</h3>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">
                  Habit name
                </label>
                <input
                  type="text"
                  value={newHabit.name}
                  onChange={(e) => setNewHabit({ ...newHabit, name: e.target.value })}
                  placeholder="e.g. Morning meditation"
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                             bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100
                             focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">
                  Category
                </label>
                <select
                  value={newHabit.category}
                  onChange={(e) => setNewHabit({ ...newHabit, category: e.target.value })}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                             bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100
                             focus:outline-none focus:ring-2 focus:ring-violet-500 capitalize"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c} className="capitalize">{c}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">
                  Description (optional)
                </label>
                <textarea
                  value={newHabit.description}
                  onChange={(e) => setNewHabit({ ...newHabit, description: e.target.value })}
                  placeholder="Why is this habit important to you?"
                  rows={2}
                  className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                             bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100
                             focus:outline-none focus:ring-2 focus:ring-violet-500 resize-none"
                />
              </div>

              <button
                onClick={() => createMutation.mutate(newHabit)}
                disabled={!newHabit.name.trim() || createMutation.isPending}
                className="w-full py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white
                           text-sm font-medium transition-colors disabled:opacity-50"
              >
                {createMutation.isPending ? "Creating…" : "Create habit"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function HabitCard({
  habit, onLog, onDelete, isLogging,
}: {
  habit: Habit;
  onLog: () => void;
  onDelete: () => void;
  isLogging: boolean;
}) {
  const categoryColors: Record<string, string> = {
    health: "text-green-600 bg-green-50 dark:bg-green-900/20",
    productivity: "text-blue-600 bg-blue-50 dark:bg-blue-900/20",
    learning: "text-violet-600 bg-violet-50 dark:bg-violet-900/20",
    mindfulness: "text-teal-600 bg-teal-50 dark:bg-teal-900/20",
    other: "text-gray-600 bg-gray-100 dark:bg-gray-800",
  };

  return (
    <div className={clsx(
      "bg-white dark:bg-gray-900 rounded-2xl border transition-all",
      habit.completed_today
        ? "border-green-200 dark:border-green-900/50 bg-green-50/30 dark:bg-green-900/5"
        : "border-gray-200 dark:border-gray-800 hover:border-violet-300"
    )}>
      <div className="flex items-center gap-4 p-4">
        {/* Complete button */}
        <button
          onClick={onLog}
          disabled={habit.completed_today || isLogging}
          className={clsx(
            "w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-all",
            habit.completed_today
              ? "bg-green-500 text-white cursor-default"
              : "border-2 border-gray-200 dark:border-gray-700 hover:border-violet-500 text-gray-300"
          )}
        >
          {habit.completed_today
            ? <CheckCircle2 size={18} />
            : <Circle size={18} />}
        </button>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className={clsx(
              "font-medium text-sm",
              habit.completed_today
                ? "text-gray-500 dark:text-gray-400 line-through"
                : "text-gray-900 dark:text-gray-100"
            )}>
              {habit.name}
            </p>
            <span className={clsx(
              "text-[10px] px-1.5 py-0.5 rounded-full font-medium capitalize",
              categoryColors[habit.category] || categoryColors.other
            )}>
              {habit.category}
            </span>
          </div>

          {/* Stats row */}
          <div className="flex items-center gap-3 mt-1">
            {habit.current_streak > 0 && (
              <div className="flex items-center gap-1">
                <Flame size={12} className="text-orange-400" />
                <span className="text-xs text-gray-500">{habit.current_streak}d</span>
              </div>
            )}
            {habit.longest_streak > 0 && (
              <div className="flex items-center gap-1">
                <Trophy size={12} className="text-amber-400" />
                <span className="text-xs text-gray-500">best: {habit.longest_streak}d</span>
              </div>
            )}
            <div className="flex items-center gap-1">
              <Target size={12} className="text-violet-400" />
              <span className="text-xs text-gray-500">{habit.completion_rate_7d}% (7d)</span>
            </div>
          </div>
        </div>

        {/* Delete */}
        <button
          onClick={onDelete}
          className="text-gray-300 hover:text-red-400 transition-colors p-1"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
}

function ProgressRing({ pct }: { pct: number }) {
  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;

  return (
    <svg width="88" height="88" className="shrink-0 -rotate-90">
      <circle cx="44" cy="44" r={r} fill="none"
        stroke="currentColor" strokeWidth="7"
        className="text-gray-100 dark:text-gray-800" />
      <circle cx="44" cy="44" r={r} fill="none"
        stroke="currentColor" strokeWidth="7"
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round"
        className="text-violet-500 transition-all duration-500" />
    </svg>
  );
}

function EmptyHabits({ onAdd }: { onAdd: () => void }) {
  return (
    <div className="text-center py-16 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-2xl">
      <Calendar size={40} className="text-gray-300 mx-auto mb-3" />
      <h3 className="text-gray-600 dark:text-gray-400 font-medium mb-1">No habits yet</h3>
      <p className="text-sm text-gray-400 mb-4">
        Start tracking daily habits to build streaks and let your AI learn your patterns.
      </p>
      <button
        onClick={onAdd}
        className="px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white
                   text-sm font-medium transition-colors"
      >
        Create your first habit
      </button>
    </div>
  );
}
