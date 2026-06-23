// ─────────────────────────────────────────────────────────────────────────────
//  AIU — Chat Page
//  Full-featured chat UI with: streaming, coach mode selector, conversation
//  sidebar, memory indicators, and real-time typing animation.
// ─────────────────────────────────────────────────────────────────────────────

import React, { useState, useRef, useEffect, useCallback } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import TextareaAutosize from "react-textarea-autosize";
import toast from "react-hot-toast";
import {
  Send, Plus, Trash2, Brain, ChevronDown,
  Zap, BookOpen, Shield, BarChart2, Loader2, Sparkles, Paperclip, Mic,
} from "lucide-react";
import { api } from "../services/apiClient";
import { useAuthStore } from "../store/authStore";
import { ThemeToggle } from "../components/ui/ThemeToggle";
import { formatDistanceToNow } from "date-fns";
import clsx from "clsx";

// ── Types ─────────────────────────────────────────────────────────────────────
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  summary: string;
  last_message_at: string;
  topics: string[];
  coach_mode: string;
  message_count: number;
}

const COACH_MODES = [
  { value: "friendly",   label: "Friendly",   icon: Zap,      desc: "Warm & encouraging" },
  { value: "mentor",     label: "Mentor",     icon: BookOpen, desc: "Wise & Socratic" },
  { value: "strict",     label: "Strict",     icon: Shield,   desc: "No-excuses coach" },
  { value: "analytical", label: "Analytical", icon: BarChart2,desc: "Data-driven advice" },
] as const;

// ── Chat Page ─────────────────────────────────────────────────────────────────
export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, isAuthenticated, accessToken } = useAuthStore();

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentConvId, setCurrentConvId] = useState<string | undefined>(conversationId);
  const [coachMode, setCoachMode] = useState<string>(
    user?.profile?.coach_mode || "friendly"
  );
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [showModeMenu, setShowModeMenu] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // ── Fetch conversation list ────────────────────────────────────────────────
  const { data: convList } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => api.listConversations().then((r) => r.data.results as Conversation[]),
    enabled: isAuthenticated,
  });

  // ── Load existing conversation ─────────────────────────────────────────────
  const { isLoading: loadingConv } = useQuery({
    queryKey: ["conversation", currentConvId],
    queryFn: async () => {
      const r = await api.getConversation(currentConvId!);
      setMessages(r.data.messages);
      return r.data;
    },
    enabled: isAuthenticated && !!currentConvId,
  });

  // ── Delete conversation ────────────────────────────────────────────────────
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      setCurrentConvId(undefined);
      setMessages([]);
      navigate("/chat");
      toast.success("Conversation archived");
    },
  });

  // ── Scroll to bottom ───────────────────────────────────────────────────────
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  // ── Start new conversation ─────────────────────────────────────────────────
  const startNew = () => {
    setCurrentConvId(undefined);
    setMessages([]);
    setStreamingContent("");
    navigate("/chat");
    inputRef.current?.focus();
  };

  // ── Send message (streaming) ───────────────────────────────────────────────
  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    setInput("");
    setIsStreaming(true);
    setStreamingContent("");

    // Optimistic user message
    const tempId = `temp-${Date.now()}`;
    const userMsg: Message = {
      id: tempId,
      role: "user",
      content: trimmed,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      abortRef.current = new AbortController();

      const apiBase = (
        (import.meta as any).env?.VITE_API_URL ||
        (import.meta as any).env?.VITE_API_BASE_URL ||
        "http://localhost:8000/api/v1"
      ).replace(/\/+$/, "");

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`;
      }

      const response = await fetch(
        `${apiBase}/ai/chat/`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({
            message: trimmed,
            conversation_id: isAuthenticated ? currentConvId : undefined,
            coach_mode: coachMode,
            stream: true,
          }),
          signal: abortRef.current.signal,
        }
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";
      let newConvId = currentConvId;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        const lines = text.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              // Streaming complete
              const assistantMsg: Message = {
                id: `assistant-${Date.now()}`,
                role: "assistant",
                content: fullContent,
                created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, assistantMsg]);
              setStreamingContent("");
              if (isAuthenticated && newConvId && newConvId !== currentConvId) {
                setCurrentConvId(newConvId);
                navigate(`/chat/${newConvId}`, { replace: true });
              }
              if (isAuthenticated) {
                queryClient.invalidateQueries({ queryKey: ["conversations"] });
              }
            } else if (data.startsWith("[ERROR]")) {
              toast.error("AI response failed. Please try again.");
            } else if (data.startsWith("{")) {
              // JSON metadata chunk (conversation_id etc.)
              try {
                const meta = JSON.parse(data);
                if (meta.conversation_id) newConvId = meta.conversation_id;
              } catch { /* non-JSON chunks */ }
            } else {
              fullContent += data;
              setStreamingContent(fullContent);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        toast.error("Failed to send message.");
        setMessages((prev) => prev.filter((m) => m.id !== tempId));
      }
    } finally {
      setIsStreaming(false);
      setStreamingContent("");
    }
  }, [accessToken, input, isAuthenticated, isStreaming, currentConvId, coachMode, navigate, queryClient]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const currentMode = COACH_MODES.find((m) => m.value === coachMode) || COACH_MODES[0];

  return (
    <div className="flex h-screen overflow-hidden bg-neutral-50 dark:bg-black">

      {/* ── Conversation Sidebar ───────────────────────────────────────────── */}
      {isAuthenticated && (
      <aside className="hidden lg:flex flex-col w-64 border-r border-gray-200 dark:border-neutral-900 bg-white dark:bg-black shrink-0">
        <div className="p-4 border-b border-gray-200 dark:border-neutral-900">
          <button
            onClick={startNew}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg
                       bg-white text-black hover:bg-neutral-200 dark:bg-white dark:hover:bg-neutral-200 text-sm font-semibold
                       transition-colors"
          >
            <Plus size={16} />
            New conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {convList?.map((conv) => (
            <button
              key={conv.id}
              onClick={() => {
                setCurrentConvId(conv.id);
                navigate(`/chat/${conv.id}`);
              }}
              className={clsx(
                "w-full text-left px-3 py-2.5 rounded-lg mb-1 group transition-colors",
                conv.id === currentConvId
                  ? "bg-gray-100 dark:bg-neutral-900 text-gray-900 dark:text-white"
                  : "hover:bg-gray-100 dark:hover:bg-neutral-900 text-gray-700 dark:text-neutral-400"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium truncate flex-1">
                  {conv.title || "New conversation"}
                </p>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(conv.id); }}
                  className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500
                             transition-opacity shrink-0"
                >
                  <Trash2 size={12} />
                </button>
              </div>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                {conv.last_message_at
                  ? formatDistanceToNow(new Date(conv.last_message_at), { addSuffix: true })
                  : "Just now"}
              </p>
              {conv.topics?.length > 0 && (
                <div className="flex gap-1 mt-1.5 flex-wrap">
                  {conv.topics.slice(0, 2).map((t) => (
                    <span key={t} className="text-[10px] px-1.5 py-0.5 rounded-full
                                             bg-gray-100 dark:bg-neutral-900 text-gray-500">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      </aside>
      )}

      {/* ── Main Chat Area ─────────────────────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-black">
          <div className="flex items-center gap-3">
            <Brain size={23} className="text-gray-900 dark:text-white" />
            <span className="sr-only">
              AIU Chat
            </span>
            {currentConvId && (
              <span className="text-xs text-gray-400 hidden sm:block">
                Memory-enhanced · {messages.length} messages
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/chat"
              className="hidden sm:inline-flex px-3 py-1.5 text-sm font-medium text-gray-700 dark:text-neutral-200"
            >
              AIU
            </Link>
            <ThemeToggle />
            {!isAuthenticated && (
              <div className="hidden sm:flex items-center gap-2 mr-2">
                <Link
                  to="/login"
                  className="px-4 py-2 rounded-full text-sm font-semibold text-gray-700
                             dark:text-white border border-gray-200 dark:border-neutral-800 hover:bg-gray-100 dark:hover:bg-neutral-950
                             transition-colors"
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 rounded-full text-sm font-semibold bg-gray-900 text-white
                             hover:bg-gray-800 dark:bg-white dark:text-black dark:hover:bg-neutral-200 transition-colors"
                >
                  Sign up
                </Link>
              </div>
            )}

          {/* Coach Mode Selector */}
          <div className="relative hidden sm:block">
            <button
              onClick={() => setShowModeMenu(!showModeMenu)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm
                         border border-gray-200 dark:border-neutral-800
                         hover:bg-gray-50 dark:hover:bg-neutral-950 transition-colors
                         text-gray-700 dark:text-neutral-300"
            >
              <currentMode.icon size={14} />
              <span className="hidden sm:inline">{currentMode.label}</span>
              <ChevronDown size={12} />
            </button>

            {showModeMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowModeMenu(false)} />
                <div className="absolute right-0 top-full mt-1 w-52 rounded-xl shadow-lg
                                bg-white dark:bg-neutral-950 border border-gray-200 dark:border-neutral-800
                                z-20 overflow-hidden">
                  {COACH_MODES.map((mode) => (
                    <button
                      key={mode.value}
                      onClick={() => { setCoachMode(mode.value); setShowModeMenu(false); }}
                      className={clsx(
                        "w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-gray-50",
                        "dark:hover:bg-neutral-900 transition-colors",
                        coachMode === mode.value && "bg-gray-50 dark:bg-neutral-900"
                      )}
                    >
                      <mode.icon size={16} className={clsx(
                        "mt-0.5 shrink-0",
                        coachMode === mode.value ? "text-gray-900 dark:text-white" : "text-gray-400"
                      )} />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {mode.label}
                        </p>
                        <p className="text-xs text-gray-500">{mode.desc}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {loadingConv && (
            <div className="flex justify-center">
              <Loader2 size={24} className="animate-spin text-violet-500" />
            </div>
          )}

          {messages.length === 0 && !loadingConv && (
            <EmptyState coachMode={currentMode} userName={user?.first_name} />
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Streaming message */}
          {isStreaming && streamingContent && (
            <MessageBubble
              message={{
                id: "streaming",
                role: "assistant",
                content: streamingContent,
                created_at: new Date().toISOString(),
              }}
              isStreaming
            />
          )}

          {/* Typing indicator */}
          {isStreaming && !streamingContent && (
            <div className="flex items-end gap-3">
              <div className="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-900/40
                              flex items-center justify-center shrink-0">
                <Brain size={14} className="text-violet-600" />
              </div>
              <div className="bg-white dark:bg-gray-900 border border-gray-200
                              dark:border-gray-700 rounded-2xl rounded-bl-sm px-4 py-3">
                <TypingDots />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="px-4 pb-8 bg-white dark:bg-black">
          <div className="max-w-3xl mx-auto">
            <div className="relative rounded-[28px] border border-gray-200 dark:border-neutral-800 bg-gray-100 dark:bg-neutral-900 shadow-sm">
              <TextareaAutosize
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="How can I help you today?"
                className="w-full resize-none rounded-[28px] border-0
                           bg-transparent px-6 py-5 pr-16
                           text-sm text-gray-900 dark:text-gray-100
                           placeholder:text-slate-500 dark:placeholder:text-slate-500
                           focus:outline-none focus:ring-0
                           max-h-48 transition-colors"
                maxRows={8}
                minRows={1}
                disabled={isStreaming}
              />
              <div className="flex items-center justify-between px-5 pb-4">
                <div className="flex items-center gap-3 text-gray-500 dark:text-neutral-400">
                  <button title="Attach file" className="p-1 hover:text-gray-900 dark:hover:text-white transition-colors">
                    <Paperclip size={18} />
                  </button>
                  <button title="Voice input" className="p-1 hover:text-gray-900 dark:hover:text-white transition-colors">
                    <Mic size={18} />
                  </button>
                </div>
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || isStreaming}
                  className="flex items-center justify-center w-10 h-10 rounded-full
                             bg-gray-300 text-gray-700 hover:bg-gray-400 dark:bg-neutral-500 dark:text-black dark:hover:bg-neutral-300 disabled:opacity-60
                             disabled:cursor-not-allowed transition-colors shrink-0"
                  title="Send"
                >
                  {isStreaming
                    ? <Loader2 size={16} className="animate-spin" />
                    : <Send size={18} />
                  }
                </button>
              </div>
            </div>
          </div>
          <div className="mt-4 mx-auto flex w-fit items-center rounded-full border border-gray-200 dark:border-neutral-800 bg-gray-100 dark:bg-neutral-900 p-1">
            {COACH_MODES.slice(0, 3).map((mode) => (
              <button
                key={mode.value}
                onClick={() => setCoachMode(mode.value)}
                className={clsx(
                  "px-4 py-1.5 rounded-full text-xs font-semibold transition-colors",
                  coachMode === mode.value
                    ? "bg-white text-black shadow-sm"
                    : "text-slate-500 hover:text-gray-900 dark:hover:text-white"
                )}
              >
                {mode.value === "mentor" ? "Focused" : mode.value === "strict" ? "Direct" : mode.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function MessageBubble({
  message,
  isStreaming = false,
}: {
  message: Message;
  isStreaming?: boolean;
}) {
  const isUser = message.role === "user";

  return (
    <div className={clsx("flex items-end gap-3", isUser && "flex-row-reverse")}>
      {/* Avatar */}
      <div className={clsx(
        "w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-medium",
        isUser
          ? "bg-violet-600 text-white"
          : "bg-violet-100 dark:bg-violet-900/40 text-violet-600"
      )}>
        {isUser ? "U" : <Brain size={14} />}
      </div>

      {/* Bubble */}
      <div className="max-w-[75%] space-y-1">
        <div className={clsx(
          "rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-violet-600 text-white rounded-br-sm"
            : "bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 rounded-bl-sm",
          isStreaming && "animate-pulse"
        )}>
          <MessageContent content={message.content} isUser={isUser} />
        </div>
        {/* Inline actions for assistant messages */}
        {!isUser && !isStreaming && (() => {
          const actions = detectInlineActions(message.content);
          return actions.length > 0 ? (
            <div className="flex gap-1.5 pl-1">
              {actions.map((action) => (
                <button key={action}
                  onClick={() => {
                    const input = document.querySelector("textarea");
                    if (input) {
                      const nativeSet = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value")?.set;
                      const prompt = action === "Add as goal"   ? "I want to make this a goal: " + message.content.slice(0, 60) + "…"
                                   : action === "Add as task"   ? "Help me create a task: " + message.content.slice(0, 60) + "…"
                                   : "Help me track this as a habit: " + message.content.slice(0, 60) + "…";
                      nativeSet?.call(input, prompt);
                      input.dispatchEvent(new Event("input", { bubbles: true }));
                      input.focus();
                    }
                  }}
                  className="text-xs px-2 py-1 rounded-lg bg-violet-50 dark:bg-violet-900/20
                             text-violet-600 dark:text-violet-400 hover:bg-violet-100 transition-colors">
                  + {action}
                </button>
              ))}
            </div>
          ) : null;
        })()}
      </div>
    </div>
  );
}

// Detect if message contains goal/task/habit mentions for inline actions
function detectInlineActions(content: string): string[] {
  const actions: string[] = [];
  if (/\bgoal\b/i.test(content)) actions.push("Add as goal");
  if (/\btask\b/i.test(content)) actions.push("Add as task");
  if (/\bhabit\b/i.test(content)) actions.push("Track habit");
  return actions.slice(0, 2);
}

function MessageContent({ content, isUser }: { content: string; isUser: boolean }) {
  // Simple markdown-like rendering
  const lines = content.split("\n");
  return (
    <div className="space-y-1">
      {lines.map((line, i) => {
        if (line.startsWith("**") && line.endsWith("**")) {
          return <p key={i} className="font-semibold">{line.slice(2, -2)}</p>;
        }
        if (line.startsWith("• ") || line.startsWith("- ")) {
          return (
            <div key={i} className="flex gap-2">
              <span className={clsx("mt-1.5 w-1.5 h-1.5 rounded-full shrink-0",
                isUser ? "bg-white/60" : "bg-violet-400")} />
              <span>{line.slice(2)}</span>
            </div>
          );
        }
        return line ? <p key={i}>{line}</p> : <br key={i} />;
      })}
    </div>
  );
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1 h-5">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="w-2 h-2 rounded-full bg-violet-400 animate-bounce"
          style={{ animationDelay: `${i * 150}ms` }}
        />
      ))}
    </div>
  );
}

function EmptyState({
  coachMode,
  userName,
}: {
  coachMode: typeof COACH_MODES[number];
  userName?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-end min-h-[34vh] px-4 pb-4">
      <div className="flex items-center gap-4 text-gray-900 dark:text-white">
        <Sparkles size={46} strokeWidth={2.25} />
        <h1 className="text-5xl font-semibold tracking-normal">
          AIU
        </h1>
      </div>
      <p className="mt-4 max-w-sm text-center text-sm text-gray-500 dark:text-neutral-500">
        {userName ? `Hi, ${userName}. ` : ""}
        {coachMode.label} mode is ready.
        {userName
          ? " Memories are active."
          : " Sign in to save memory."}
      </p>
    </div>
  );
}
