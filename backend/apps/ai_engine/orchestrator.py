"""
AIU — AI Engine: Core Orchestrator
The central AI system that:
1. Retrieves relevant memories (RAG)
2. Builds context-aware prompts
3. Calls the LLM with retry/fallback
4. Post-processes and stores responses
5. Extracts insights asynchronously
"""

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Generator

import backoff

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone

from apps.memory.models import Conversation, MemoryEmbedding, MemoryInsight, Message
from apps.users.models import UserProfile

from .prompts import PromptBuilder
from .embeddings import EmbeddingService
from .llm_client import LLMClient

logger = logging.getLogger("ai_engine")

AI_SETTINGS = settings.AI_ENGINE


@dataclass
class AIRequest:
    """Typed request object for the AI orchestrator."""
    user_id: str
    message: str
    conversation_id: str | None = None
    coach_mode: str = "friendly"
    stream: bool = False
    extra_context: dict = field(default_factory=dict)


@dataclass
class AIResponse:
    """Typed response from the AI orchestrator."""
    content: str
    conversation_id: str
    message_id: str
    tokens_used: int
    model: str
    retrieved_memories: int
    latency_ms: float
    cached: bool = False


class MemoryManager:
    """
    Multi-layer memory:
    - L1: Redis short-term (session context, recent messages)
    - L2: PostgreSQL long-term structured memory
    """

    SHORT_TERM_TTL = AI_SETTINGS["SHORT_TERM_TTL"]
    TOP_K = AI_SETTINGS["LONG_TERM_TOP_K"]

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.embedding_service = EmbeddingService()

    # ── Short-term memory (Redis) ─────────────────────────────────────────────

    def _short_term_key(self, conversation_id: str) -> str:
        return f"aiu:stm:{self.user_id}:{conversation_id}"

    def get_short_term(self, conversation_id: str) -> list[dict]:
        """Retrieve recent messages from Redis session cache."""
        key = self._short_term_key(conversation_id)
        cached = cache.get(key)
        return cached if cached is not None else []

    def set_short_term(self, conversation_id: str, messages: list[dict]) -> None:
        key = self._short_term_key(conversation_id)
        # Keep only last N messages
        messages = messages[-AI_SETTINGS["CONTEXT_WINDOW_MESSAGES"]:]
        cache.set(key, messages, timeout=self.SHORT_TERM_TTL)

    def append_short_term(self, conversation_id: str, role: str, content: str) -> None:
        messages = self.get_short_term(conversation_id)
        messages.append({"role": role, "content": content})
        self.set_short_term(conversation_id, messages)

    def clear_short_term(self, conversation_id: str) -> None:
        cache.delete(self._short_term_key(conversation_id))


    def retrieve_relevant_memories(self, query: str, top_k: int | None = None) -> list[str]:
        """
        Embed the query, then find top-k semantically similar memory chunks.
        Returns list of content strings to inject into prompt context.
        """
        top_k = top_k or self.TOP_K
        query_embedding = self.embedding_service.embed(query)

        import math

        def cosine_sim(a, b):
            if not a or not b or len(a) != len(b):
                return 0.0
            dot = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x * x for x in a)) or 1
            mag_b = math.sqrt(sum(x * x for x in b)) or 1
            return dot / (mag_a * mag_b)

        candidates = (
            MemoryEmbedding.objects
            .filter(user_id=self.user_id)
            .exclude(embedding_json=[])
            .order_by("-importance_score", "-created_at")[:200]
        )

        if not candidates:
            # Fallback: most important recent memories
            return list(
                MemoryEmbedding.objects.filter(user_id=self.user_id)
                .order_by("-importance_score", "-created_at")
                .values_list("content", flat=True)[:top_k]
            )

        scored = sorted(
            [(cosine_sim(query_embedding, m.embedding_json), m) for m in candidates],
            key=lambda x: x[0], reverse=True,
        )[:top_k]

        now = timezone.now()
        ids = [m.id for _, m in scored]
        MemoryEmbedding.objects.filter(id__in=ids).update(
            access_count=models.F("access_count") + 1,
            last_accessed=now,
        )

        return [m.content for _, m in scored]

    def store_memory(
        self,
        content: str,
        source_type: str,
        source_id: uuid.UUID,
        importance: float = 0.5,
    ) -> MemoryEmbedding | None:
        """Embed and store a new memory chunk. Deduplicates by content hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check for existing identical memory
        if MemoryEmbedding.objects.filter(
            user_id=self.user_id, content_hash=content_hash
        ).exists():
            return None

        embedding = self.embedding_service.embed(content)
        return MemoryEmbedding.objects.create(
            user_id=self.user_id,
            source_type=source_type,
            source_id=source_id,
            content=content,
            content_hash=content_hash,
            embedding_json=embedding,
            importance_score=importance,
        )

    def get_user_insights(self) -> list[str]:
        """Retrieve active insights to include in system prompt."""
        insights = MemoryInsight.objects.filter(
            user_id=self.user_id,
            is_active=True,
        ).order_by("-confidence")[:20]
        return [f"[{i.insight_type}] {i.content}" for i in insights]


# LLMClient imported from llm_client.py

class AIOrchestrator:
    """
    Main entry point for all AI requests.
    Coordinates: memory retrieval → prompt building → LLM call → storage → async tasks.
    """

    def __init__(self):
        self.llm = LLMClient()
        self.prompt_builder = PromptBuilder()

    def process(self, req: AIRequest) -> AIResponse:
        """
        Full pipeline: retrieve → build → call → store.
        """
        start = time.perf_counter()
        memory_mgr = MemoryManager(req.user_id)

        # ── 1. Ensure conversation exists ─────────────────────────────────────
        conversation = self._get_or_create_conversation(req)

        # ── 2. Retrieve relevant long-term memories ───────────────────────────
        retrieved = memory_mgr.retrieve_relevant_memories(req.message)
        logger.debug("Memory retrieval", extra={"count": len(retrieved), "user": req.user_id})

        # ── 3. Retrieve recent short-term context ─────────────────────────────
        recent_messages = memory_mgr.get_short_term(str(conversation.id))

        # ── 4. Get user insights ──────────────────────────────────────────────
        insights = memory_mgr.get_user_insights()

        # ── 5. Load user profile ──────────────────────────────────────────────
        try:
            profile = UserProfile.objects.select_related("user").get(user_id=req.user_id)
        except UserProfile.DoesNotExist:
            profile = None

        # ── 6. Build prompt messages ──────────────────────────────────────────
        messages = self.prompt_builder.build(
            user_message=req.message,
            recent_messages=recent_messages,
            retrieved_memories=retrieved,
            user_insights=insights,
            coach_mode=req.coach_mode,
            user_profile=profile,
            extra_context=req.extra_context,
        )

        # ── 7. Call LLM ───────────────────────────────────────────────────────
        llm_response = self.llm.complete(messages)

        latency_ms = (time.perf_counter() - start) * 1000

        # ── 8. Persist user message ───────────────────────────────────────────
        user_msg = Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content=req.message,
            model_used=llm_response["model"],
        )

        # ── 9. Persist assistant message ──────────────────────────────────────
        assistant_msg = Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=llm_response["content"],
            prompt_tokens=llm_response["prompt_tokens"],
            completion_tokens=llm_response["completion_tokens"],
            model_used=llm_response["model"],
        )

        # ── 10. Update short-term memory ──────────────────────────────────────
        memory_mgr.append_short_term(str(conversation.id), "user", req.message)
        memory_mgr.append_short_term(str(conversation.id), "assistant", llm_response["content"])

        # ── 11. Update conversation metadata ──────────────────────────────────
        Conversation.objects.filter(pk=conversation.pk).update(
            last_message_at=timezone.now()
        )

        # ── 12. Dispatch async tasks ──────────────────────────────────────────
        from .tasks import (
            store_message_embedding,
            extract_insights_from_conversation,
            update_behavior_patterns,
        )
        store_message_embedding.delay(str(user_msg.id), req.message, req.user_id)
        store_message_embedding.delay(
            str(assistant_msg.id), llm_response["content"], req.user_id
        )
        # Run insight extraction every 5 messages
        msg_count = conversation.messages.count()
        if msg_count % 5 == 0:
            extract_insights_from_conversation.delay(str(conversation.id))
        update_behavior_patterns.delay(req.user_id, "ai_query", {"hour": timezone.now().hour})

        return AIResponse(
            content=llm_response["content"],
            conversation_id=str(conversation.id),
            message_id=str(assistant_msg.id),
            tokens_used=llm_response["prompt_tokens"] + llm_response["completion_tokens"],
            model=llm_response["model"],
            retrieved_memories=len(retrieved),
            latency_ms=round(latency_ms, 2),
        )

    def _get_or_create_conversation(self, req: AIRequest) -> Conversation:
        if req.conversation_id:
            try:
                return Conversation.objects.get(
                    id=req.conversation_id, user_id=req.user_id
                )
            except Conversation.DoesNotExist:
                pass
        return Conversation.objects.create(
            user_id=req.user_id,
            coach_mode=req.coach_mode,
        )

    def stream(self, req: AIRequest) -> Generator[str, None, None]:
        """
        Streaming variant. Yields text chunks as they arrive.
        Stores the complete response after iteration.
        """
        memory_mgr = MemoryManager(req.user_id)
        conversation = self._get_or_create_conversation(req)
        retrieved = memory_mgr.retrieve_relevant_memories(req.message)
        recent_messages = memory_mgr.get_short_term(str(conversation.id))
        insights = memory_mgr.get_user_insights()

        try:
            profile = UserProfile.objects.get(user_id=req.user_id)
        except UserProfile.DoesNotExist:
            profile = None

        messages = self.prompt_builder.build(
            user_message=req.message,
            recent_messages=recent_messages,
            retrieved_memories=retrieved,
            user_insights=insights,
            coach_mode=req.coach_mode,
            user_profile=profile,
            extra_context=req.extra_context,
        )

        full_response = []
        stream = self.llm.complete(messages, stream=True)

        for chunk in stream:
            delta = getattr(chunk.choices[0].delta, "content", None)
            if delta:
                full_response.append(delta)
                yield delta

        # Store complete response after stream ends
        complete_content = "".join(full_response)
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.USER,
            content=req.message,
        )
        Message.objects.create(
            conversation=conversation,
            role=Message.Role.ASSISTANT,
            content=complete_content,
        )
        memory_mgr.append_short_term(str(conversation.id), "user", req.message)
        memory_mgr.append_short_term(str(conversation.id), "assistant", complete_content)
        Conversation.objects.filter(pk=conversation.pk).update(last_message_at=timezone.now())


# Singleton instance (thread-safe, stateless after init)
orchestrator = AIOrchestrator()
