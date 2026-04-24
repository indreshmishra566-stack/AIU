// ─────────────────────────────────────────────────────────────────────────────
//  AIU — useChat hook
//  Manages full chat state: messages, streaming, conversation lifecycle.
//  Extracted from ChatPage for reusability and testability.
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "./useApi";
import { useAuthStore } from "../store/authStore";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

interface UseChatOptions {
  conversationId?: string;
  coachMode?: string;
}

export function useChat({ conversationId, coachMode = "friendly" }: UseChatOptions = {}) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { accessToken } = useAuthStore();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentConvId, setCurrentConvId] = useState<string | undefined>(conversationId);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  const getApiBase = () => {
    const env = (import.meta as any).env || {};
    const base =
      env.VITE_API_URL ||
      env.VITE_API_BASE_URL ||
      "http://localhost:8000/api/v1";
    return base.replace(/\/+$/, "");
  };

  const sendMessage = useCallback(
    async (input: string, extraContext?: Record<string, unknown>) => {
      const trimmed = input.trim();
      if (!trimmed || isStreaming) return;

      setError(null);
      setIsStreaming(true);
      setStreamingContent("");

      // Optimistic user message
      const tempId = `temp-${Date.now()}`;
      const userMsg: ChatMessage = {
        id: tempId,
        role: "user",
        content: trimmed,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      try {
        abortRef.current = new AbortController();

        const response = await fetch(`${getApiBase()}/ai/chat/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            message: trimmed,
            conversation_id: currentConvId,
            coach_mode: coachMode,
            stream: true,
            context: extraContext ?? {},
          }),
          signal: abortRef.current.signal,
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.message || `HTTP ${response.status}`);
        }

        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let fullContent = "";
        let newConvId = currentConvId;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const text = decoder.decode(value, { stream: true });
          for (const line of text.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6);

            if (data === "[DONE]") {
              // Commit assistant message
              const assistantMsg: ChatMessage = {
                id: `assistant-${Date.now()}`,
                role: "assistant",
                content: fullContent,
                created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, assistantMsg]);
              setStreamingContent("");

              if (newConvId && newConvId !== currentConvId) {
                setCurrentConvId(newConvId);
                navigate(`/chat/${newConvId}`, { replace: true });
              }
              queryClient.invalidateQueries({ queryKey: QUERY_KEYS.conversations });
            } else if (data.startsWith("[ERROR]")) {
              throw new Error(data.slice(7).trim() || "AI response failed.");
            } else {
              // Try JSON metadata, otherwise treat as text chunk
              try {
                const meta = JSON.parse(data);
                if (meta.conversation_id) newConvId = meta.conversation_id;
              } catch {
                fullContent += data;
                setStreamingContent(fullContent);
              }
            }
          }
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Unknown error";
        if (msg !== "AbortError" && !msg.includes("abort")) {
          setError(msg);
          // Roll back optimistic message
          setMessages((prev) => prev.filter((m) => m.id !== tempId));
        }
      } finally {
        setIsStreaming(false);
        setStreamingContent("");
      }
    },
    [isStreaming, currentConvId, coachMode, accessToken, navigate, queryClient]
  );

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setCurrentConvId(undefined);
    setStreamingContent("");
    setError(null);
  }, []);

  const loadMessages = useCallback((msgs: ChatMessage[]) => {
    setMessages(msgs);
  }, []);

  return {
    messages,
    currentConvId,
    isStreaming,
    streamingContent,
    error,
    sendMessage,
    stopStreaming,
    clearMessages,
    loadMessages,
    setCurrentConvId,
  };
}
