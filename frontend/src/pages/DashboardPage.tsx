// ─────────────────────────────────────────────────────────────────────────────
//  AIU — Dashboard Page
//  Shows: stats overview, habit streak, activity heatmap, recent insights,
//         AI recommendations, productivity windows.
// ─────────────────────────────────────────────────────────────────────────────

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  BarChart2, Brain, CheckCircle2, Flame, TrendingUp,
  MessageSquare, Lightbulb, Sparkles, ArrowRight, Target,
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { api } from "../services/apiClient";
import { useAuthStore } from "../store/authStore";
import { format } from "date-fns";

export default function DashboardPage() {
  const { user } = useAuthStore();

  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => api.getDashboardStats().then((r) => r.data.data),
    refetchInterval: 1000 * 60 * 5,
  });

  const { data: goals } = useQuery({
    queryKey: ["goals-active"],
    queryFn: () => api.activeGoals().then((r) => r.data.results),
  });

  const { data: recommendations } = useQuery({
    queryKey: ["recommendations", "pending"],
    queryFn: () =>
      api.listRecommendations("pending").then((r) => r.data.results?.slice(0, 3)),
  });

  const { data: nudges } = useQuery({
    queryKey: ["nudges"],
    queryFn: () => api.getNudges().then((r) => r.data.nudges),
    refetchInterval: 1000 * 60 * 10, // refresh every 10 min
  });

  const { data: insights } = useQuery({
    queryKey: ["insights"],
    queryFn: () => api.getInsights().then((r) => r.data.results?.slice(0, 4)),
  });

  // Build hourly activity data for chart
  const activityData = React.useMemo(() => {
    const heatmap = stats?.activity?.heatmap_by_hour || {};
    return Array.from({ length: 24 }, (_, h) => ({
      hour: `${h}:00`,
      activity: heatmap[String(h)] || 0,
    }));
  }, [stats]);

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  })();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {greeting}{user?.first_name ? `, ${user.first_name}` : ""}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            {format(new Date(), "EEEE, MMMM d")} · Your AI is always learning
          </p>
        </div>
        <Link
          to="/chat"
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600
                     hover:bg-violet-700 text-white text-sm font-medium transition-colors"
        >
          <Brain size={16} />
          Open AI
        </Link>
      </div>

      {/* ── Smart Nudges ──────────────────────────────────────────────────── */}
      {nudges && nudges.length > 0 && (
        <div className="space-y-2">
          {nudges.map((nudge: any, i: number) => (
            <div key={i} className={`flex items-start gap-3 px-4 py-3 rounded-xl border text-sm ${
              nudge.type === "warning"       ? "bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-900/30"
            : nudge.type === "encouragement" ? "bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-900/30"
            : nudge.type === "reminder"      ? "bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-900/30"
            : "bg-blue-50 dark:bg-blue-900/10 border-blue-200 dark:border-blue-900/30"
            }`}>
              <span className="text-base shrink-0 mt-0.5">{nudge.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 dark:text-gray-100">{nudge.title}</p>
                <p className="text-gray-500 dark:text-gray-400 mt-0.5 text-xs">{nudge.message}</p>
              </div>
              {nudge.action && (
                <Link to={nudge.action.path}
                  className="text-xs text-violet-600 dark:text-violet-400 hover:underline shrink-0 font-medium">
                  {nudge.action.label} →
                </Link>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── Stats Row ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Target size={20} className="text-violet-500" />}
          label="Active goals"
          value={isLoading ? "—" : String(goals?.filter((g: any) => g.status === "active").length ?? 0)}
          sub="in progress"
          color="violet"
        />
        <StatCard
          icon={<CheckCircle2 size={20} className="text-green-500" />}
          label="Avg. progress"
          value={isLoading ? "—" : `${goals?.length ? Math.round(goals.reduce((s: number, g: any) => s + g.progress_pct, 0) / goals.length) : 0}%`}
          sub="across goals"
          color="green"
        />
        <StatCard
          icon={<MessageSquare size={20} className="text-violet-500" />}
          label="Conversations"
          value={isLoading ? "—" : String(stats?.conversations?.total ?? 0)}
          sub={`${stats?.conversations?.last_7_days ?? 0} this week`}
          color="violet"
        />
        <StatCard
          icon={<Lightbulb size={20} className="text-amber-500" />}
          label="Insights"
          value={isLoading ? "—" : String(stats?.insights?.total ?? 0)}
          sub="about you"
          color="amber"
        />
      </div>

      {/* ── Main Grid ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Activity Heatmap */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-2xl border
                        border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                Activity by hour
              </h3>
              <p className="text-xs text-gray-500 mt-0.5">Past 7 days</p>
            </div>
            <BarChart2 size={18} className="text-gray-400" />
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={activityData} barCategoryGap="20%">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(107,114,128,0.1)" />
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 10, fill: "currentColor" }}
                tickLine={false}
                interval={3}
                className="text-gray-400"
              />
              <YAxis hide />
              <Tooltip
                contentStyle={{
                  background: "var(--bg-card, #fff)",
                  border: "1px solid rgba(107,114,128,0.2)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
              />
              <Bar dataKey="activity" fill="#7c3aed" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>

          {/* Productive hours */}
          {stats?.activity?.productive_hours?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800">
              <p className="text-xs text-gray-500 mb-2">Peak productivity hours</p>
              <div className="flex gap-2 flex-wrap">
                {stats.activity.productive_hours.slice(0, 5).map((h: number) => (
                  <span key={h} className="text-xs px-2 py-1 rounded-lg
                                           bg-violet-50 dark:bg-violet-900/20 text-violet-700
                                           dark:text-violet-300 font-medium">
                    {h}:00
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Insights Panel */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border
                        border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">
              What I know about you
            </h3>
            <Link to="/insights" className="text-xs text-violet-600 hover:underline">
              View all
            </Link>
          </div>

          {insights?.length ? (
            <div className="space-y-3">
              {insights.map((insight: any) => (
                <div key={insight.id} className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-violet-400 mt-1.5 shrink-0" />
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-snug">
                      {insight.content}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5 capitalize">
                      {insight.insight_type} · {Math.round(insight.confidence * 100)}% confidence
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <Brain size={32} className="text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-400">
                Have a few conversations and I'll start building insights about you.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── Active Goals Snapshot ────────────────────────────────────────── */}
      {goals && goals.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Target size={18} className="text-violet-500" />
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">Active Goals</h3>
            </div>
            <Link to="/goals" className="text-xs text-violet-600 hover:underline flex items-center gap-1">
              All goals <ArrowRight size={11} />
            </Link>
          </div>
          <div className="space-y-3">
            {goals.slice(0, 3).map((goal: any) => (
              <div key={goal.id} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{goal.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                      <div className="bg-violet-500 h-1.5 rounded-full" style={{ width: `${goal.progress_pct}%` }} />
                    </div>
                    <span className="text-xs text-gray-500 shrink-0">{goal.progress_pct}%</span>
                  </div>
                </div>
                {goal.days_remaining !== null && goal.days_remaining !== undefined && (
                  <span className={`text-xs shrink-0 ${goal.days_remaining < 7 ? "text-red-500" : "text-gray-400"}`}>
                    {goal.days_remaining < 0 ? "Overdue" : `${goal.days_remaining}d`}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Recommendations ────────────────────────────────────────────────── */}
      {recommendations?.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border
                        border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles size={18} className="text-amber-500" />
              <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                AI Recommendations
              </h3>
            </div>
            <Link to="/recommendations" className="text-xs text-violet-600 hover:underline">
              View all
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {recommendations.map((rec: any) => (
              <RecommendationCard key={rec.id} rec={rec} />
            ))}
          </div>
        </div>
      )}

      {/* ── Habit Consistency ──────────────────────────────────────────────── */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border
                      border-gray-200 dark:border-gray-800 p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">
            Habit consistency
          </h3>
          <Link
            to="/habits"
            className="flex items-center gap-1 text-xs text-violet-600 hover:underline"
          >
            Manage habits <ArrowRight size={12} />
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-violet-500 to-violet-600 h-3 rounded-full transition-all"
              style={{
                width: `${stats?.activity?.habit_consistency_score || 0}%`,
              }}
            />
          </div>
          <span className="text-2xl font-bold text-gray-900 dark:text-gray-100 w-16 text-right">
            {stats?.activity?.habit_consistency_score || 0}%
          </span>
        </div>
        {stats?.activity?.behavior_summary && (
          <p className="text-sm text-gray-500 mt-3">
            {stats.activity.behavior_summary}
          </p>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatCard({
  icon, label, value, sub, color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    orange: "bg-orange-50 dark:bg-orange-900/10",
    green:  "bg-green-50 dark:bg-green-900/10",
    violet: "bg-violet-50 dark:bg-violet-900/10",
    amber:  "bg-amber-50 dark:bg-amber-900/10",
  };

  return (
    <div className={`rounded-2xl p-5 ${colorMap[color] || ""}`}>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
          {label}
        </span>
      </div>
      <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{sub}</p>
    </div>
  );
}

function RecommendationCard({ rec }: { rec: any }) {
  const priorityColors: Record<string, string> = {
    high:   "text-red-600 bg-red-50 dark:bg-red-900/10",
    medium: "text-amber-600 bg-amber-50 dark:bg-amber-900/10",
    low:    "text-green-600 bg-green-50 dark:bg-green-900/10",
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-xl p-4
                    hover:border-violet-300 transition-colors">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 leading-snug">
          {rec.title}
        </h4>
        <span className={`text-[10px] px-2 py-0.5 rounded-full shrink-0 font-medium
                         ${priorityColors[rec.priority] || ""}`}>
          {rec.priority}
        </span>
      </div>
      <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">
        {rec.description}
      </p>
    </div>
  );
}
