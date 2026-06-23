// ─────────────────────────────────────────────────────────────────────────────
//  AIU — Insights Page (Full)
//  Behavior patterns, performance trends, weakness identification,
//  habit analysis, personalized recommendations with charts.
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../services/apiClient";
import {
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import { Lightbulb, TrendingUp, AlertTriangle, Sparkles, Brain, Target, Flame } from "lucide-react";
import clsx from "clsx";

const TYPE_COLORS: Record<string, string> = {
  personality:  "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300",
  behavior:     "bg-blue-100   text-blue-700   dark:bg-blue-900/30   dark:text-blue-300",
  preference:   "bg-amber-100  text-amber-700  dark:bg-amber-900/30  dark:text-amber-300",
  goal:         "bg-green-100  text-green-700  dark:bg-green-900/30  dark:text-green-300",
  skill:        "bg-teal-100   text-teal-700   dark:bg-teal-900/30   dark:text-teal-300",
  challenge:    "bg-red-100    text-red-700    dark:bg-red-900/30    dark:text-red-400",
  relationship: "bg-pink-100   text-pink-700   dark:bg-pink-900/30   dark:text-pink-300",
};

export default function InsightsPage() {
  const [activeTab, setActiveTab] = useState<"patterns" | "trends" | "weaknesses" | "recommendations">("patterns");

  const { data: stats }    = useQuery({ queryKey: ["dashboard-stats"],      queryFn: () => api.getDashboardStats().then(r => r.data.data) });
  const { data: insights } = useQuery({ queryKey: ["insights-all"],         queryFn: () => api.getInsights().then(r => r.data.results) });
  const { data: recs }     = useQuery({ queryKey: ["recommendations", "pending"], queryFn: () => api.listRecommendations("pending").then(r => r.data.results) });
  const { data: timeline } = useQuery({
    queryKey: ["behavior-timeline", 30],
    queryFn:  () => api.getBehaviorTimeline(30).then(r => r.data.events),
    enabled:  activeTab === "trends",
  });

  const hourlyData = React.useMemo(() => {
    const heatmap = stats?.activity?.heatmap_by_hour || {};
    return Array.from({ length: 24 }, (_, h) => ({ hour: `${h}:00`, activity: heatmap[String(h)] || 0 }));
  }, [stats]);

  const radarData = React.useMemo(() => {
    const breakdown = stats?.insights?.breakdown || [];
    const typeMap: Record<string, number> = {};
    breakdown.forEach((b: any) => { typeMap[b.insight_type] = b.count; });
    return [
      { subject: "Behavior",    value: typeMap.behavior    || 0 },
      { subject: "Personality", value: typeMap.personality || 0 },
      { subject: "Skills",      value: typeMap.skill       || 0 },
      { subject: "Goals",       value: typeMap.goal        || 0 },
      { subject: "Challenges",  value: typeMap.challenge   || 0 },
      { subject: "Preferences", value: typeMap.preference  || 0 },
    ];
  }, [stats]);

  const weaknesses  = insights?.filter((i: any) => i.insight_type === "challenge") ?? [];
  const behaviorIns = insights?.filter((i: any) => i.insight_type === "behavior")  ?? [];
  const allOther    = insights?.filter((i: any) => !["challenge","behavior"].includes(i.insight_type)) ?? [];

  const tabs = [
    { key: "patterns",        label: "Patterns",        icon: Brain },
    { key: "trends",          label: "Trends",          icon: TrendingUp },
    { key: "weaknesses",      label: "Weaknesses",      icon: AlertTriangle },
    { key: "recommendations", label: "Recommendations", icon: Sparkles },
  ] as const;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Insights</h1>
        <p className="text-sm text-gray-500 mt-1">
          What AIU has learned about you — {insights?.length ?? 0} insights collected
        </p>
      </div>

      {/* Stat pills */}
      <div className="flex gap-3 mb-6 flex-wrap">
        {[
          { icon: Brain,         label: "Total insights",  val: insights?.length ?? 0,                            color: "violet" },
          { icon: Target,        label: "Goal insights",   val: (insights?.filter((i:any)=>i.insight_type==="goal")?.length ?? 0), color: "green" },
          { icon: AlertTriangle, label: "Challenges",      val: weaknesses.length,                                color: "red"    },
          { icon: Flame,         label: "Consistency",     val: `${stats?.activity?.habit_consistency_score ?? 0}%`, color: "amber" },
        ].map(({ icon: Icon, label, val, color }) => (
          <div key={label} className={clsx(
            "flex items-center gap-2 px-4 py-2 rounded-xl text-sm",
            color === "violet" && "bg-violet-50 dark:bg-violet-900/20 text-violet-700 dark:text-violet-300",
            color === "green"  && "bg-green-50  dark:bg-green-900/20  text-green-700  dark:text-green-300",
            color === "red"    && "bg-red-50    dark:bg-red-900/20    text-red-700    dark:text-red-300",
            color === "amber"  && "bg-amber-50  dark:bg-amber-900/20  text-amber-700  dark:text-amber-300",
          )}>
            <Icon size={14} /><span className="font-semibold">{val}</span><span className="opacity-70">{label}</span>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-800 mb-6">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setActiveTab(key)}
            className={clsx(
              "flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors",
              activeTab === key
                ? "border-violet-500 text-violet-600 dark:text-violet-400"
                : "border-transparent text-gray-400 hover:text-gray-600"
            )}>
            <Icon size={14} />{label}
          </button>
        ))}
      </div>

      {/* PATTERNS */}
      {activeTab === "patterns" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">Activity by hour</h3>
              <p className="text-xs text-gray-500 mb-4">When you're most active</p>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={hourlyData} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(107,114,128,0.1)" />
                  <XAxis dataKey="hour" tick={{ fontSize: 9 }} tickLine={false} interval={5} />
                  <YAxis hide />
                  <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="activity" fill="#7c3aed" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              {stats?.activity?.productive_hours?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
                  <p className="text-xs text-gray-500 mb-1.5">Peak hours</p>
                  <div className="flex gap-1.5 flex-wrap">
                    {stats.activity.productive_hours.slice(0,5).map((h: number) => (
                      <span key={h} className="text-xs px-2 py-0.5 rounded-lg bg-violet-50 dark:bg-violet-900/20 text-violet-700 dark:text-violet-300 font-medium">{h}:00</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">Self-knowledge map</h3>
              <p className="text-xs text-gray-500 mb-2">Breadth of insights collected</p>
              <ResponsiveContainer width="100%" height={180}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(107,114,128,0.15)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
                  <Radar name="Insights" dataKey="value" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Behavior patterns</h3>
            {behaviorIns.length === 0
              ? <p className="text-sm text-gray-400">Chat more to build behavior patterns.</p>
              : <div className="space-y-2">{behaviorIns.map((ins: any) => <InsightRow key={ins.id} insight={ins} />)}</div>
            }
          </div>

          {allOther.length > 0 && (
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">All insights</h3>
              <div className="space-y-2">{allOther.map((ins: any) => <InsightRow key={ins.id} insight={ins} />)}</div>
            </div>
          )}
        </div>
      )}

      {/* TRENDS */}
      {activeTab === "trends" && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Performance summary</h3>
            <p className="text-sm text-gray-500 mb-4">{stats?.activity?.behavior_summary || "Keep chatting and logging to build a performance profile."}</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label: "Conversations",  val: stats?.conversations?.total ?? 0 },
                { label: "Messages",       val: stats?.conversations?.total_messages ?? 0 },
                { label: "AI sentiment",   val: stats?.conversations?.avg_sentiment ? (stats.conversations.avg_sentiment > 0 ? "Positive" : "Neutral") : "—" },
                { label: "Consistency",    val: `${stats?.activity?.habit_consistency_score ?? 0}%` },
              ].map(({ label, val }) => (
                <div key={label} className="bg-gray-50 dark:bg-gray-800 rounded-xl p-3 text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{val}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{label}</p>
                </div>
              ))}
            </div>
          </div>

          {timeline && (() => {
            const counts: Record<string, number> = {};
            timeline.forEach((e: any) => { counts[e.event_type] = (counts[e.event_type] || 0) + 1; });
            const chartData = Object.entries(counts).map(([type, count]) => ({ type: type.replace(/_/g, " "), count })).sort((a, b) => b.count - a.count);
            return (
              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Activity breakdown (30 days)</h3>
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={chartData} layout="vertical" margin={{ left: 60 }}>
                    <XAxis type="number" hide />
                    <YAxis type="category" dataKey="type" tick={{ fontSize: 11 }} width={110} />
                    <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="count" fill="#7c3aed" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            );
          })()}
        </div>
      )}

      {/* WEAKNESSES */}
      {activeTab === "weaknesses" && (
        <div className="space-y-4">
          <div className="bg-red-50 dark:bg-red-900/10 border border-red-200 dark:border-red-900/30 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle size={16} className="text-red-500" />
              <h3 className="font-semibold text-red-700 dark:text-red-400">Identified challenges</h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Patterns AIU has noticed that may be holding you back. Awareness is the first step.</p>
          </div>

          {weaknesses.length === 0 ? (
            <div className="text-center py-16 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-2xl">
              <AlertTriangle size={36} className="text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-400">No challenges identified yet. Keep chatting.</p>
            </div>
          ) : weaknesses.map((ins: any) => (
            <div key={ins.id} className="bg-white dark:bg-gray-900 border border-red-200 dark:border-red-900/40 rounded-2xl p-5">
              <div className="flex gap-3">
                <div className="w-2 h-2 rounded-full bg-red-400 mt-1.5 shrink-0" />
                <div>
                  <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">{ins.content}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-xs text-red-400">{Math.round(ins.confidence * 100)}% confidence</span>
                    <span className="text-xs text-gray-400">· {ins.evidence_count} observations</span>
                  </div>
                </div>
              </div>
            </div>
          ))}

          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">Habit consistency</h3>
            <div className="flex items-center gap-4">
              <div className="flex-1 bg-gray-100 dark:bg-gray-800 rounded-full h-3">
                <div className={clsx("h-3 rounded-full transition-all",
                    (stats?.activity?.habit_consistency_score ?? 0) >= 70 ? "bg-green-500"
                  : (stats?.activity?.habit_consistency_score ?? 0) >= 40 ? "bg-amber-500" : "bg-red-500"
                )} style={{ width: `${stats?.activity?.habit_consistency_score ?? 0}%` }} />
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-gray-100">{stats?.activity?.habit_consistency_score ?? 0}%</span>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {(stats?.activity?.habit_consistency_score ?? 0) >= 70 ? "Strong — keep it up!" : (stats?.activity?.habit_consistency_score ?? 0) >= 40 ? "Moderate — room to grow." : "Low — try focusing on one habit at a time."}
            </p>
          </div>
        </div>
      )}

      {/* RECOMMENDATIONS */}
      {activeTab === "recommendations" && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-1">
            <Sparkles size={16} className="text-amber-500" />
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Personalized for you</h3>
          </div>
          {!recs?.length ? (
            <div className="text-center py-16 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-2xl">
              <Sparkles size={36} className="text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-400">Recommendations appear after a few conversations.</p>
            </div>
          ) : recs.map((rec: any) => (
            <div key={rec.id} className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{rec.title}</h4>
                    <span className={clsx("text-[10px] px-1.5 py-0.5 rounded-full font-medium capitalize",
                      rec.priority === "high" ? "bg-red-100 text-red-700" : rec.priority === "medium" ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-600"
                    )}>{rec.priority}</span>
                  </div>
                  <p className="text-sm text-gray-500 leading-relaxed">{rec.description}</p>
                </div>
                <span className="text-xs px-2 py-1 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-500 capitalize shrink-0">{rec.category}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InsightRow({ insight }: { insight: any }) {
  return (
    <div className="flex gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
      <div className="w-2 h-2 rounded-full bg-violet-400 mt-1.5 shrink-0" />
      <div className="flex-1">
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{insight.content}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className={clsx("text-[11px] px-1.5 py-0.5 rounded-full font-medium capitalize",
            TYPE_COLORS[insight.insight_type] || "bg-gray-100 text-gray-500")}>{insight.insight_type}</span>
          <span className="text-xs text-gray-400">{Math.round(insight.confidence * 100)}%</span>
          <span className="text-xs text-gray-400">· {insight.evidence_count} sources</span>
        </div>
      </div>
    </div>
  );
}
