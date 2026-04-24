// ─────────────────────────────────────────────────────────────────────────────
//  AIU — Goals Page
//  Structured growth system: create goals, add milestones, track progress,
//  complete tasks, get AI advice, view activity history.
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/apiClient";
import toast from "react-hot-toast";
import {
  Plus, Target, CheckCircle2, Circle, ChevronDown, ChevronRight,
  Sparkles, Clock, Flame, Trophy, X, Loader2, Activity,
  ArrowRight, MoreHorizontal, Flag, ListChecks,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import clsx from "clsx";

// ── Types ─────────────────────────────────────────────────────────────────────
interface GoalTask   { id: string; title: string; status: string; due_date?: string; }
interface Milestone  { id: string; title: string; is_completed: boolean; order: number; target_date?: string; tasks: GoalTask[]; }
interface Goal {
  id: string; title: string; description: string; category: string;
  priority: string; status: string; progress_pct: number; target_date?: string;
  ai_recommendation: string; extracted_from_chat: boolean;
  current_streak: number; longest_streak: number;
  milestones: Milestone[];
  tasks?: GoalTask[];
  milestone_count: { total: number; completed: number };
  task_count: { total: number; done: number };
  days_remaining?: number;
  created_at: string;
}

const CATEGORIES = [
  { value: "health",      label: "Health & Fitness",  color: "text-green-600  bg-green-50  dark:bg-green-900/20" },
  { value: "career",      label: "Career & Work",      color: "text-blue-600   bg-blue-50   dark:bg-blue-900/20" },
  { value: "learning",    label: "Learning & Skills",  color: "text-violet-600 bg-violet-50 dark:bg-violet-900/20" },
  { value: "finance",     label: "Finance",            color: "text-amber-600  bg-amber-50  dark:bg-amber-900/20" },
  { value: "mindfulness", label: "Mindfulness",        color: "text-teal-600   bg-teal-50   dark:bg-teal-900/20" },
  { value: "social",      label: "Relationships",      color: "text-pink-600   bg-pink-50   dark:bg-pink-900/20" },
  { value: "creative",    label: "Creative",           color: "text-orange-600 bg-orange-50 dark:bg-orange-900/20" },
  { value: "other",       label: "Other",              color: "text-gray-600   bg-gray-100  dark:bg-gray-800" },
];

const PRIORITY_COLORS: Record<string, string> = {
  high:   "text-red-600   bg-red-50   dark:bg-red-900/20",
  medium: "text-amber-600 bg-amber-50 dark:bg-amber-900/20",
  low:    "text-gray-500  bg-gray-100 dark:bg-gray-800",
};

export default function GoalsPage() {
  const qc = useQueryClient();
  const [showNewGoal, setShowNewGoal]     = useState(false);
  const [selectedGoal, setSelectedGoal]  = useState<Goal | null>(null);
  const [statusFilter, setStatusFilter]  = useState("active");

  const { data: goals, isLoading } = useQuery({
    queryKey: ["goals", statusFilter],
    queryFn: () => api.listGoals(statusFilter).then((r) => r.data.results as Goal[]),
  });

  const createMutation = useMutation({
    mutationFn: (data: object) => api.createGoal(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals"] });
      setShowNewGoal(false);
      toast.success("Goal created!");
    },
    onError: () => toast.error("Failed to create goal."),
  });

  const activeCount    = goals?.filter((g) => g.status === "active").length ?? 0;
  const completedCount = goals?.filter((g) => g.status === "completed").length ?? 0;
  const avgProgress    = goals?.length
    ? Math.round(goals.reduce((s, g) => s + g.progress_pct, 0) / goals.length)
    : 0;

  return (
    <div className="flex h-full overflow-hidden">

      {/* ── Goals List ─────────────────────────────────────────────────────── */}
      <div className={clsx(
        "flex flex-col border-r border-gray-200 dark:border-gray-800 transition-all",
        selectedGoal ? "w-80 shrink-0" : "flex-1"
      )}>
        {/* Header */}
        <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">Goals</h1>
            <button
              onClick={() => setShowNewGoal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-sm font-medium
                         bg-violet-600 hover:bg-violet-700 text-white transition-colors"
            >
              <Plus size={15} /> New Goal
            </button>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: "Active",    val: activeCount },
              { label: "Completed", val: completedCount },
              { label: "Avg. progress", val: `${avgProgress}%` },
            ].map(({ label, val }) => (
              <div key={label} className="bg-gray-50 dark:bg-gray-800 rounded-xl p-2 text-center">
                <p className="text-lg font-bold text-gray-900 dark:text-gray-100">{val}</p>
                <p className="text-[10px] text-gray-400">{label}</p>
              </div>
            ))}
          </div>

          {/* Status filter */}
          <div className="flex gap-1 mt-3">
            {["active", "paused", "completed", "all"].map((s) => (
              <button key={s} onClick={() => setStatusFilter(s === "all" ? "" : s)}
                className={clsx(
                  "flex-1 py-1 rounded-lg text-xs font-medium capitalize transition-colors",
                  (statusFilter === s || (s === "all" && !statusFilter))
                    ? "bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300"
                    : "text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
                )}>
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {isLoading ? (
            [...Array(3)].map((_, i) => (
              <div key={i} className="h-24 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
            ))
          ) : goals?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Target size={40} className="text-gray-300 mb-3" />
              <p className="font-medium text-gray-600 dark:text-gray-400">No goals yet</p>
              <p className="text-sm text-gray-400 mt-1 mb-4">Create a goal or ask AIU in Chat.</p>
              <button onClick={() => setShowNewGoal(true)}
                className="px-4 py-2 rounded-xl bg-violet-600 text-white text-sm font-medium hover:bg-violet-700">
                Create first goal
              </button>
            </div>
          ) : goals?.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              isSelected={selectedGoal?.id === goal.id}
              onClick={() => setSelectedGoal(selectedGoal?.id === goal.id ? null : goal)}
            />
          ))}
        </div>
      </div>

      {/* ── Goal Detail Panel ─────────────────────────────────────────────── */}
      {selectedGoal && (
        <GoalDetail
          goalId={selectedGoal.id}
          onClose={() => setSelectedGoal(null)}
        />
      )}

      {/* ── New Goal Modal ────────────────────────────────────────────────── */}
      {showNewGoal && (
        <NewGoalModal
          onClose={() => setShowNewGoal(false)}
          onSubmit={(data) => createMutation.mutate(data)}
          isLoading={createMutation.isPending}
        />
      )}
    </div>
  );
}

// ── Goal Card ─────────────────────────────────────────────────────────────────

function GoalCard({ goal, isSelected, onClick }: {
  goal: Goal; isSelected: boolean; onClick: () => void;
}) {
  const cat = CATEGORIES.find((c) => c.value === goal.category);

  return (
    <button onClick={onClick} className={clsx(
      "w-full text-left p-4 rounded-2xl border transition-all",
      isSelected
        ? "border-violet-400 bg-violet-50 dark:bg-violet-900/20"
        : "border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hover:border-violet-300"
    )}>
      {/* Title + priority */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <p className="font-medium text-sm text-gray-900 dark:text-gray-100 leading-snug line-clamp-2">
          {goal.title}
        </p>
        <span className={clsx("text-[10px] px-1.5 py-0.5 rounded-full font-medium shrink-0 capitalize",
          PRIORITY_COLORS[goal.priority])}>
          {goal.priority}
        </span>
      </div>

      {/* Category + streak */}
      <div className="flex items-center gap-2 mb-3">
        <span className={clsx("text-[10px] px-1.5 py-0.5 rounded-full font-medium", cat?.color)}>
          {cat?.label}
        </span>
        {goal.current_streak > 0 && (
          <span className="flex items-center gap-0.5 text-[10px] text-orange-500">
            <Flame size={10} /> {goal.current_streak}d
          </span>
        )}
        {goal.extracted_from_chat && (
          <span className="text-[10px] text-violet-400">✦ from chat</span>
        )}
      </div>

      {/* Progress bar */}
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-full h-1.5">
          <div
            className="bg-violet-500 h-1.5 rounded-full transition-all"
            style={{ width: `${goal.progress_pct}%` }}
          />
        </div>
        <span className="text-xs text-gray-500 w-8 text-right">{goal.progress_pct}%</span>
      </div>

      {/* Milestone count + days left */}
      <div className="flex items-center justify-between mt-2">
        <span className="text-[11px] text-gray-400">
          {goal.milestone_count.completed}/{goal.milestone_count.total} milestones
        </span>
        {goal.days_remaining !== undefined && goal.days_remaining !== null && (
          <span className={clsx("text-[11px]",
            goal.days_remaining < 7 ? "text-red-500" : "text-gray-400")}>
            {goal.days_remaining < 0
              ? "Overdue"
              : goal.days_remaining === 0
              ? "Due today"
              : `${goal.days_remaining}d left`}
          </span>
        )}
      </div>
    </button>
  );
}

// ── Goal Detail Panel ─────────────────────────────────────────────────────────

function GoalDetail({ goalId, onClose }: { goalId: string; onClose: () => void }) {
  const qc = useQueryClient();
  const [activeTab, setActiveTab]  = useState<"milestones" | "tasks" | "activity" | "ai">("milestones");
  const [showAddMS, setShowAddMS]  = useState(false);
  const [showAddTask, setShowAddTask] = useState(false);
  const [newMS, setNewMS]   = useState({ title: "", target_date: "" });
  const [newTask, setNewTask] = useState({ title: "", due_date: "" });
  const [loadingAdvice, setLoadingAdvice] = useState(false);

  const { data: goal, isLoading } = useQuery<Goal>({
    queryKey: ["goal", goalId],
    queryFn: () => api.getGoal(goalId).then((r) => r.data.data || r.data),
  });

  const completeMilestoneMut = useMutation({
    mutationFn: (msId: string) => api.completeMilestone(goalId, msId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["goal", goalId] }); qc.invalidateQueries({ queryKey: ["goals"] }); toast.success("Milestone complete! 🎉"); },
  });

  const addMilestoneMut = useMutation({
    mutationFn: (data: object) => api.addMilestone(goalId, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["goal", goalId] }); setShowAddMS(false); setNewMS({ title: "", target_date: "" }); toast.success("Milestone added!"); },
  });

  const addTaskMut = useMutation({
    mutationFn: (data: object) => api.addGoalTask(goalId, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["goal", goalId] }); setShowAddTask(false); setNewTask({ title: "", due_date: "" }); toast.success("Task added!"); },
  });

  const completeTaskMut = useMutation({
    mutationFn: (taskId: string) => api.completeGoalTask(goalId, taskId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["goal", goalId] }); toast.success("Task done!"); },
  });

  const getAdvice = async () => {
    setLoadingAdvice(true);
    try {
      await api.getGoalAiAdvice(goalId);
      qc.invalidateQueries({ queryKey: ["goal", goalId] });
      toast.success("AI advice generated!");
      setActiveTab("ai");
    } catch { toast.error("Failed to get AI advice."); }
    finally { setLoadingAdvice(false); }
  };

  const completeGoalMut = useMutation({
    mutationFn: () => api.completeGoal(goalId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["goals"] }); qc.invalidateQueries({ queryKey: ["goal", goalId] }); toast.success("Goal completed! 🏆"); },
  });

  const { data: activities } = useQuery<Array<{ id: string; description: string; occurred_at: string }>>({
    queryKey: ["goal-activity", goalId],
    queryFn: () => api.getGoalActivity(goalId).then((r) => r.data.activities),
    enabled: activeTab === "activity",
  });

  if (isLoading) return (
    <div className="flex-1 flex items-center justify-center bg-white dark:bg-gray-900">
      <Loader2 size={28} className="animate-spin text-violet-500" />
    </div>
  );
  if (!goal) return null;

  const cat = CATEGORIES.find((c) => c.value === goal.category);

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-gray-900 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium", cat?.color)}>{cat?.label}</span>
              <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium capitalize", PRIORITY_COLORS[goal.priority])}>{goal.priority}</span>
              {goal.extracted_from_chat && <span className="text-xs text-violet-400">✦ from chat</span>}
            </div>
            <h2 className="font-bold text-gray-900 dark:text-gray-100 text-lg leading-snug">{goal.title}</h2>
            {goal.description && <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">{goal.description}</p>}
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button onClick={getAdvice} disabled={loadingAdvice}
              className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-medium
                         bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400
                         hover:bg-amber-100 transition-colors disabled:opacity-50">
              {loadingAdvice ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
              AI Advice
            </button>
            <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-full h-2.5">
            <div className="bg-gradient-to-r from-violet-500 to-violet-600 h-2.5 rounded-full transition-all"
              style={{ width: `${goal.progress_pct}%` }} />
          </div>
          <span className="text-sm font-bold text-gray-900 dark:text-gray-100 w-10 text-right">
            {goal.progress_pct}%
          </span>
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <ListChecks size={11} /> {goal.milestone_count.completed}/{goal.milestone_count.total} milestones
          </span>
          {goal.current_streak > 0 && (
            <span className="flex items-center gap-1 text-orange-400">
              <Flame size={11} /> {goal.current_streak}d streak
            </span>
          )}
          {goal.days_remaining !== undefined && goal.days_remaining !== null && (
            <span className={clsx("flex items-center gap-1", goal.days_remaining < 7 ? "text-red-400" : "")}>
              <Clock size={11} /> {goal.days_remaining < 0 ? "Overdue" : `${goal.days_remaining}d left`}
            </span>
          )}
          {goal.status !== "completed" && (
            <button onClick={() => completeGoalMut.mutate()}
              className="ml-auto flex items-center gap-1 text-green-600 hover:text-green-700 font-medium">
              <Trophy size={11} /> Mark complete
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-800 px-4">
        {(["milestones", "tasks", "activity", "ai"] as const).map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={clsx(
              "px-4 py-2.5 text-sm font-medium capitalize border-b-2 transition-colors",
              activeTab === tab
                ? "border-violet-500 text-violet-600"
                : "border-transparent text-gray-400 hover:text-gray-600"
            )}>
            {tab === "ai" ? "AI Advice" : tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-5">

        {/* ── Milestones ── */}
        {activeTab === "milestones" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Milestones</h3>
              <button onClick={() => setShowAddMS(true)}
                className="flex items-center gap-1 text-xs text-violet-600 hover:text-violet-700 font-medium">
                <Plus size={12} /> Add
              </button>
            </div>

            {showAddMS && (
              <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-3 space-y-2">
                <input value={newMS.title} onChange={(e) => setNewMS({ ...newMS, title: e.target.value })}
                  placeholder="Milestone title…" autoFocus
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500" />
                <input type="date" value={newMS.target_date} onChange={(e) => setNewMS({ ...newMS, target_date: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500" />
                <div className="flex gap-2">
                  <button onClick={() => addMilestoneMut.mutate(newMS)} disabled={!newMS.title.trim() || addMilestoneMut.isPending}
                    className="px-3 py-1.5 rounded-lg bg-violet-600 text-white text-xs font-medium hover:bg-violet-700 disabled:opacity-50">
                    {addMilestoneMut.isPending ? "Adding…" : "Add milestone"}
                  </button>
                  <button onClick={() => setShowAddMS(false)} className="px-3 py-1.5 rounded-lg text-xs text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700">Cancel</button>
                </div>
              </div>
            )}

            {goal.milestones.length === 0 ? (
              <p className="text-sm text-gray-400 py-4 text-center">No milestones yet. Break your goal into steps.</p>
            ) : (
              goal.milestones.map((ms) => (
                <div key={ms.id} className={clsx(
                  "flex items-start gap-3 p-3 rounded-xl border transition-all",
                  ms.is_completed
                    ? "border-green-200 dark:border-green-900/50 bg-green-50/40 dark:bg-green-900/5"
                    : "border-gray-200 dark:border-gray-800"
                )}>
                  <button onClick={() => !ms.is_completed && completeMilestoneMut.mutate(ms.id)}
                    disabled={ms.is_completed}
                    className={clsx("mt-0.5 shrink-0 transition-colors",
                      ms.is_completed ? "text-green-500 cursor-default" : "text-gray-300 hover:text-violet-500")}>
                    {ms.is_completed ? <CheckCircle2 size={18} /> : <Circle size={18} />}
                  </button>
                  <div className="flex-1">
                    <p className={clsx("text-sm font-medium",
                      ms.is_completed ? "line-through text-gray-400" : "text-gray-800 dark:text-gray-200")}>
                      {ms.title}
                    </p>
                    {ms.target_date && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        Due {format(new Date(ms.target_date), "MMM d, yyyy")}
                      </p>
                    )}
                    {ms.tasks.length > 0 && (
                      <p className="text-xs text-gray-400 mt-0.5">
                        {ms.tasks.filter((task: GoalTask) => task.status === "done").length}/{ms.tasks.length} tasks
                      </p>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* ── Tasks ── */}
        {activeTab === "tasks" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Tasks</h3>
              <button onClick={() => setShowAddTask(true)}
                className="flex items-center gap-1 text-xs text-violet-600 hover:text-violet-700 font-medium">
                <Plus size={12} /> Add
              </button>
            </div>

            {showAddTask && (
              <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-3 space-y-2">
                <input value={newTask.title} onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                  placeholder="Task title…" autoFocus
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500" />
                <input type="date" value={newTask.due_date} onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500" />
                <div className="flex gap-2">
                  <button onClick={() => addTaskMut.mutate(newTask)} disabled={!newTask.title.trim() || addTaskMut.isPending}
                    className="px-3 py-1.5 rounded-lg bg-violet-600 text-white text-xs font-medium hover:bg-violet-700 disabled:opacity-50">
                    {addTaskMut.isPending ? "Adding…" : "Add task"}
                  </button>
                  <button onClick={() => setShowAddTask(false)} className="px-3 py-1.5 rounded-lg text-xs text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-700">Cancel</button>
                </div>
              </div>
            )}

            {goal.tasks?.length === 0 ? (
              <p className="text-sm text-gray-400 py-4 text-center">No tasks yet.</p>
            ) : (
              goal.tasks?.map((task: GoalTask) => (
                <div key={task.id} className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 dark:border-gray-800">
                  <button onClick={() => task.status !== "done" && completeTaskMut.mutate(task.id)}
                    disabled={task.status === "done"}
                    className={clsx("shrink-0", task.status === "done" ? "text-green-500 cursor-default" : "text-gray-300 hover:text-violet-500")}>
                    {task.status === "done" ? <CheckCircle2 size={16} /> : <Circle size={16} />}
                  </button>
                  <span className={clsx("text-sm flex-1", task.status === "done" && "line-through text-gray-400")}>
                    {task.title}
                  </span>
                  {task.due_date && (
                    <span className="text-xs text-gray-400">{format(new Date(task.due_date), "MMM d")}</span>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* ── Activity ── */}
        {activeTab === "activity" && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Activity History</h3>
            {!activities?.length ? (
              <p className="text-sm text-gray-400 py-4 text-center">No activity yet.</p>
            ) : (
              activities.map((act: { id: string; description: string; occurred_at: string }) => (
                <div key={act.id} className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-violet-400 mt-1.5 shrink-0" />
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{act.description}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {formatDistanceToNow(new Date(act.occurred_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* ── AI Advice ── */}
        {activeTab === "ai" && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Sparkles size={16} className="text-amber-500" />
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">AI Advice for this Goal</h3>
            </div>
            {goal.ai_recommendation ? (
              <div className="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-900/30 rounded-xl p-4">
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                  {goal.ai_recommendation}
                </p>
              </div>
            ) : (
              <div className="text-center py-10">
                <Sparkles size={32} className="text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-400 mb-4">No AI advice yet for this goal.</p>
                <button onClick={getAdvice} disabled={loadingAdvice}
                  className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium disabled:opacity-50 transition-colors">
                  {loadingAdvice ? "Generating…" : "Get AI advice"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── New Goal Modal ─────────────────────────────────────────────────────────────

function NewGoalModal({ onClose, onSubmit, isLoading }: {
  onClose: () => void;
  onSubmit: (data: object) => void;
  isLoading: boolean;
}) {
  const [form, setForm] = useState({
    title: "", description: "", category: "other",
    priority: "medium", target_date: "",
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">New goal</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1"><X size={18} /></button>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="text-sm text-gray-500 mb-1 block">What do you want to achieve?</label>
            <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="e.g. Run a 5K by June" autoFocus
              className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 text-gray-900 dark:text-gray-100" />
          </div>
          <div>
            <label className="text-sm text-gray-500 mb-1 block">Description (optional)</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2} placeholder="Why is this goal important to you?"
              className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 text-gray-900 dark:text-gray-100 resize-none" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm text-gray-500 mb-1 block">Category</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 text-gray-900 dark:text-gray-100">
                {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-500 mb-1 block">Priority</label>
              <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 text-gray-900 dark:text-gray-100">
                {["low","medium","high"].map((p) => <option key={p} value={p} className="capitalize">{p}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-sm text-gray-500 mb-1 block">Target date (optional)</label>
            <input type="date" value={form.target_date} onChange={(e) => setForm({ ...form, target_date: e.target.value })}
              className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 text-gray-900 dark:text-gray-100" />
          </div>
          <button onClick={() => onSubmit(form)} disabled={!form.title.trim() || isLoading}
            className="w-full py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-medium text-sm transition-colors disabled:opacity-50">
            {isLoading ? "Creating…" : "Create goal"}
          </button>
        </div>
      </div>
    </div>
  );
}
