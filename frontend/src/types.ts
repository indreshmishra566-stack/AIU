// ─────────────────────────────────────────────────────────────────────────────
//  AIU — Shared TypeScript Types
//  Single source of truth for all data models used across the frontend.
// ─────────────────────────────────────────────────────────────────────────────

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface UserProfile {
  coach_mode: CoachMode;
  timezone: string;
  language: string;
  personality_traits: Record<string, unknown>;
  behavior_patterns: BehaviorPatterns;
  productivity_windows: number[];
  communication_style: string;
  onboarding_completed: boolean;
  goals: string[];
  total_interactions: number;
  ai_satisfaction_score: number;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: "user" | "premium" | "admin" | "staff";
  is_email_verified: boolean;
  date_joined: string;
  last_activity: string | null;
  profile: UserProfile | null;
}

export type CoachMode = "friendly" | "mentor" | "strict" | "analytical";

// ── Chat / Memory ─────────────────────────────────────────────────────────────

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  intent?: string;
  sentiment?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  model_used?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  summary: string;
  coach_mode: CoachMode;
  topics: string[];
  sentiment_score: number | null;
  importance_score: number;
  is_archived: boolean;
  started_at: string;
  last_message_at: string | null;
  message_count: number;
}

export interface MemoryInsight {
  id: string;
  insight_type: InsightType;
  content: string;
  confidence: number;
  evidence_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type InsightType =
  | "personality"
  | "behavior"
  | "preference"
  | "goal"
  | "skill"
  | "challenge"
  | "relationship";

// ── Goals ─────────────────────────────────────────────────────────────────────

export interface Goal {
  id: string;
  title: string;
  description: string;
  category: GoalCategory;
  priority: Priority;
  status: GoalStatus;
  progress_pct: number;
  target_date?: string;
  started_at: string;
  completed_at?: string;
  ai_recommendation: string;
  extracted_from_chat: boolean;
  current_streak: number;
  longest_streak: number;
  milestones: Milestone[];
  tasks?: GoalTask[];
  milestone_count: { total: number; completed: number };
  task_count: { total: number; done: number };
  days_remaining?: number;
  created_at: string;
  updated_at: string;
}

export type GoalStatus   = "active" | "paused" | "completed" | "abandoned";
export type GoalCategory = "health" | "career" | "learning" | "finance" | "mindfulness" | "social" | "creative" | "other";
export type Priority     = "low" | "medium" | "high";

export interface Milestone {
  id: string;
  title: string;
  description: string;
  is_completed: boolean;
  order: number;
  target_date?: string;
  completed_at?: string;
  created_at: string;
  tasks: GoalTask[];
}

export interface GoalTask {
  id: string;
  title: string;
  status: "todo" | "in_progress" | "done" | "skipped";
  due_date?: string;
  notes: string;
  completed_at?: string;
  created_at: string;
}

export interface GoalActivity {
  id: string;
  activity_type: string;
  description: string;
  metadata: Record<string, unknown>;
  occurred_at: string;
}

// ── Analytics ────────────────────────────────────────────────────────────────

export interface DashboardStats {
  habits: {
    active_count: number;
    completed_today: number;
    completion_30d: number;
    top_streak: number;
  };
  conversations: {
    total: number;
    last_7_days: number;
    total_messages: number;
    avg_sentiment: number;
  };
  insights: {
    total: number;
    breakdown: { insight_type: InsightType; count: number }[];
  };
  activity: {
    heatmap_by_hour: Record<string, number>;
    productive_hours: number[];
    habit_consistency_score: number;
    behavior_summary: string;
  };
  goals?: {
    active_count: number;
    avg_progress: number;
    completed_count: number;
  };
}

export interface BehaviorPatterns {
  habit_consistency_score: number;
  top_categories: string[];
  summary: string;
  analyzed_at?: string;
}

export interface BehaviorEvent {
  event_type: string;
  occurred_at: string;
  hour_of_day: number;
  day_of_week: number;
}

// ── Recommendations ───────────────────────────────────────────────────────────

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: Priority;
  status: "pending" | "accepted" | "dismissed" | "completed";
  rationale: string;
  confidence_score: number;
  created_at: string;
  acted_on_at?: string;
}

// ── AI Chat ───────────────────────────────────────────────────────────────────

export interface AIResponse {
  content: string;
  conversation_id: string;
  message_id: string;
  tokens_used: number;
  model: string;
  retrieved_memories: number;
  latency_ms: number;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  coach_mode?: CoachMode;
  stream?: boolean;
  context?: Record<string, unknown>;
}

// ── API responses ─────────────────────────────────────────────────────────────

export interface APISuccess<T> {
  status: "success";
  data: T;
}

export interface APIList<T> {
  status: "success";
  results: T[];
  pagination?: {
    count: number;
    next: string | null;
    previous: string | null;
    page: number;
    total_pages: number;
  };
}

export interface APIError {
  status: "error";
  code: number;
  message: string;
  errors: Record<string, string[]> | null;
  request_id: string;
}

// ── UI helpers ────────────────────────────────────────────────────────────────

export type LoadingState = "idle" | "loading" | "success" | "error";

export interface SelectOption {
  value: string;
  label: string;
  color?: string;
}
