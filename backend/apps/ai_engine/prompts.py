"""
AIU — AI Engine: Prompt Templates & Builder
Modular prompt construction with memory injection, coach modes, and user context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.users.models import UserProfile


# ── Coach Mode Personas ───────────────────────────────────────────────────────

COACH_PERSONAS: dict[str, str] = {
    "friendly": """
You are a warm, encouraging personal AI companion. You celebrate wins, gently challenge
limiting beliefs, and always make the user feel supported. Use conversational language.
Avoid jargon. Ask clarifying questions when needed.
""".strip(),

    "mentor": """
You are a wise, experienced mentor. You draw on deep knowledge to provide nuanced guidance.
You ask Socratic questions to help the user discover answers themselves. You balance
encouragement with honest, direct feedback. You think long-term.
""".strip(),

    "strict": """
You are a high-performance coach with zero tolerance for excuses. You hold the user to the
highest standards they've set for themselves. You call out rationalizations directly but
respectfully. You focus on outcomes, accountability, and discipline. No hand-holding.
""".strip(),

    "analytical": """
You are a rigorous analytical advisor. You break problems into components, identify patterns,
quantify where possible, and recommend data-driven approaches. You present pros/cons before
recommending. You acknowledge uncertainty explicitly.
""".strip(),
}

SYSTEM_PROMPT_TEMPLATE = """
{persona}

## Who you are talking to
{user_context}

## What you know about this person (long-term memory)
{insights_section}

## Relevant memories from past conversations
{memories_section}

## Core operating principles
- You are NOT a generic chatbot. You are a personalised AI that knows this specific person.
- Reference past conversations and insights naturally when relevant.
- Your goal is the user's genuine long-term flourishing, not just immediate satisfaction.
- Be concise unless depth is requested. Respect the user's time.
- If you detect distress or mental health concerns, respond with empathy and suggest
  professional resources where appropriate.
- Never make up facts. Say "I'm not sure" when uncertain.
- Format responses with light markdown (bold for emphasis, bullets for lists) but avoid
  excessive structure in casual conversation.

## Current session context
{session_context}
""".strip()

USER_CONTEXT_TEMPLATE = """
Name: {name}
Goals: {goals}
Communication style: {style}
Timezone: {timezone}
""".strip()

NO_PROFILE_CONTEXT = "New user — building profile from this conversation."


class PromptBuilder:
    """
    Builds the message list for the LLM call.
    Injects: system persona + user profile + insights + retrieved memories + recent messages.
    """

    def build(
        self,
        user_message: str,
        recent_messages: list[dict],
        retrieved_memories: list[str],
        user_insights: list[str],
        coach_mode: str = "friendly",
        user_profile: "UserProfile | None" = None,
        extra_context: dict | None = None,
    ) -> list[dict]:
        """
        Returns a list of { role, content } dicts ready for the LLM.
        Structure: [system, ...recent_messages, user_message]
        """
        system_content = self._build_system(
            coach_mode=coach_mode,
            user_profile=user_profile,
            retrieved_memories=retrieved_memories,
            user_insights=user_insights,
            recent_messages=recent_messages,
            extra_context=extra_context or {},
        )

        messages: list[dict] = [{"role": "system", "content": system_content}]

        # Inject recent conversation history (excluding the current message)
        for msg in recent_messages:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # The current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def _build_system(
        self,
        coach_mode: str,
        user_profile: "UserProfile | None",
        retrieved_memories: list[str],
        user_insights: list[str],
        recent_messages: list[dict],
        extra_context: dict,
    ) -> str:
        persona = COACH_PERSONAS.get(coach_mode, COACH_PERSONAS["friendly"])

        # User context block
        if user_profile:
            user_ctx = USER_CONTEXT_TEMPLATE.format(
                name=user_profile.user.full_name,
                goals=", ".join(user_profile.goals[:5]) or "Not set",
                style=user_profile.communication_style,
                timezone=user_profile.timezone,
            )
        else:
            user_ctx = NO_PROFILE_CONTEXT

        # Insights block
        if user_insights:
            insights_section = "\n".join(f"• {insight}" for insight in user_insights[:10])
        else:
            insights_section = "No insights collected yet — this is an early conversation."

        # Memories block
        if retrieved_memories:
            memories_section = "\n".join(
                f"[Memory {i+1}] {mem}" for i, mem in enumerate(retrieved_memories)
            )
        else:
            memories_section = "No relevant memories found for this query."

        # Session context
        session_lines = []
        if extra_context.get("current_habits"):
            session_lines.append(f"Active habits: {', '.join(extra_context['current_habits'])}")
        if extra_context.get("mood"):
            session_lines.append(f"User's reported mood: {extra_context['mood']}")
        if extra_context.get("decision_context"):
            session_lines.append(f"Decision context: {extra_context['decision_context']}")
        session_context = "\n".join(session_lines) or "No additional session context."

        return SYSTEM_PROMPT_TEMPLATE.format(
            persona=persona,
            user_context=user_ctx,
            insights_section=insights_section,
            memories_section=memories_section,
            session_context=session_context,
        )

    def build_insight_extraction_prompt(self, conversation_text: str) -> list[dict]:
        """
        Prompt for extracting structured insights from a conversation.
        Returns insights as JSON.
        """
        system = """
You are an expert at extracting structured insights about a person from their conversations.
Analyze the conversation and extract meaningful insights about the person's:
personality traits, behavior patterns, goals, challenges, preferences, and skills.

Respond ONLY with a JSON array of insight objects with these fields:
{
  "insight_type": "personality|behavior|preference|goal|skill|challenge|relationship",
  "content": "Clear, specific statement about the person",
  "confidence": 0.0-1.0
}

Be specific and evidence-based. Only include insights with confidence >= 0.6.
Maximum 10 insights per conversation.
""".strip()

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Conversation:\n\n{conversation_text}"},
        ]

    def build_summary_prompt(self, messages_text: str) -> list[dict]:
        """Build a prompt to summarize a conversation."""
        return [
            {
                "role": "system",
                "content": "Summarize this conversation in 2-3 sentences. Focus on key topics, decisions, and insights.",
            },
            {"role": "user", "content": messages_text},
        ]

    def build_behavior_analysis_prompt(self, events_summary: str) -> list[dict]:
        """Analyze behavioral patterns from event data."""
        return [
            {
                "role": "system",
                "content": """
Analyze the user's behavioral event data and identify meaningful patterns.
Return a JSON object with:
{
  "productive_hours": [list of most active hours 0-23],
  "habit_consistency_score": 0-100,
  "top_categories": ["list", "of", "categories"],
  "behavioral_summary": "2-sentence summary of patterns"
}
""".strip(),
            },
            {"role": "user", "content": f"Events data:\n{events_summary}"},
        ]
