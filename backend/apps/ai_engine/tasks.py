"""
AIU — AI Engine: Celery Background Tasks
Async processing for: embeddings, insight extraction, behavior analysis,
conversation summarization, recommendation generation.
"""

import json
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger("ai_engine")


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="embeddings",
    name="ai_engine.store_message_embedding",
)
def store_message_embedding(self, message_id: str, content: str, user_id: str):
    """Embed a message and store it for future retrieval."""
    try:
        from apps.ai_engine.embeddings import EmbeddingService
        from apps.memory.models import MemoryEmbedding
        import hashlib

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if MemoryEmbedding.objects.filter(user_id=user_id, content_hash=content_hash).exists():
            return {"status": "skipped", "reason": "duplicate"}

        embedding_svc = EmbeddingService()
        vector = embedding_svc.embed(content)

        MemoryEmbedding.objects.create(
            user_id=user_id,
            source_type="message",
            source_id=message_id,
            content=content,
            content_hash=content_hash,
            embedding_json=vector,
            importance_score=0.5,
        )
        return {"status": "stored", "message_id": message_id}

    except Exception as exc:
        logger.exception("Failed to store embedding", extra={"message_id": message_id})
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    queue="ai_processing",
    name="ai_engine.extract_insights_from_conversation",
)
def extract_insights_from_conversation(self, conversation_id: str):
    """Extract structured insights from a completed conversation segment."""
    try:
        from apps.memory.models import Conversation, Message, MemoryInsight
        from apps.ai_engine.orchestrator import LLMClient
        from apps.ai_engine.prompts import PromptBuilder

        conversation = Conversation.objects.select_related("user").get(id=conversation_id)
        messages = Message.objects.filter(conversation=conversation).order_by("created_at")

        if messages.count() < 3:
            return {"status": "skipped", "reason": "too_few_messages"}

        # Build conversation text
        conv_text = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in messages
        )

        prompt_builder = PromptBuilder()
        llm = LLMClient()
        messages_payload = prompt_builder.build_insight_extraction_prompt(conv_text)
        response = llm.complete(messages_payload, max_tokens=2000, temperature=0.1)

        # Parse JSON insights
        raw = response["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        insights_data = json.loads(raw)

        created_count = 0
        for item in insights_data:
            if item.get("confidence", 0) < 0.6:
                continue
            obj, created = MemoryInsight.objects.get_or_create(
                user=conversation.user,
                insight_type=item["insight_type"],
                content=item["content"],
                defaults={
                    "confidence": item["confidence"],
                    "source_conversations": [str(conversation_id)],
                },
            )
            if not created:
                # Reinforce existing insight atomically to avoid lost updates
                # when two workers process related conversations concurrently.
                from django.db import transaction
                from django.db.models import F
                with transaction.atomic():
                    locked = (
                        MemoryInsight.objects.select_for_update().get(pk=obj.pk)
                    )
                    locked.confidence = min(
                        1.0,
                        (locked.confidence + item["confidence"]) / 2 + 0.05,
                    )
                    locked.source_conversations = list(
                        set(locked.source_conversations + [str(conversation_id)])
                    )[:20]
                    locked.save(update_fields=["confidence", "source_conversations"])
                    MemoryInsight.objects.filter(pk=obj.pk).update(
                        evidence_count=F("evidence_count") + 1
                    )
            else:
                created_count += 1

        # Generate conversation summary
        summarize_conversation.delay(conversation_id)

        # Extract goals from this conversation
        extract_goals_from_conversation.delay(conversation_id, str(conversation.user.id))

        logger.info(
            "Insights extracted",
            extra={"conversation_id": conversation_id, "new_insights": created_count},
        )
        return {"status": "success", "new_insights": created_count}

    except Exception as exc:
        logger.exception("Insight extraction failed", extra={"conversation_id": conversation_id})
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=2,
    queue="ai_processing",
    name="ai_engine.summarize_conversation",
)
def summarize_conversation(self, conversation_id: str):
    """Generate and store a conversation summary."""
    try:
        from apps.memory.models import Conversation, Message
        from apps.ai_engine.orchestrator import LLMClient
        from apps.ai_engine.prompts import PromptBuilder

        conversation = Conversation.objects.get(id=conversation_id)
        messages = Message.objects.filter(conversation=conversation).order_by("created_at")
        conv_text = "\n".join(f"{m.role}: {m.content[:200]}" for m in messages)

        llm = LLMClient()
        builder = PromptBuilder()
        response = llm.complete(builder.build_summary_prompt(conv_text), max_tokens=200)
        summary = response["content"].strip()

        # Extract topics from summary keywords
        topics = _extract_topics(summary)

        Conversation.objects.filter(pk=conversation.pk).update(
            summary=summary,
            topics=topics,
        )
        return {"status": "success"}

    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    queue="analytics",
    name="ai_engine.update_behavior_patterns",
)
def update_behavior_patterns(self, user_id: str, event_type: str, payload: dict):
    """Log a behavior event and trigger pattern analysis if thresholds met."""
    try:
        from apps.habits.models import BehaviorEvent
        from django.utils import timezone as tz

        now = tz.now()
        BehaviorEvent.objects.create(
            user_id=user_id,
            event_type=event_type,
            payload=payload,
            hour_of_day=now.hour,
            day_of_week=now.weekday(),
        )

        # Trigger full analysis if enough new events
        event_count = BehaviorEvent.objects.filter(
            user_id=user_id,
        ).count()
        if event_count % 50 == 0:
            analyze_user_behavior.delay(user_id)

        return {"status": "logged"}

    except Exception as exc:
        logger.exception("Behavior event logging failed")
        return {"status": "error", "error": str(exc)}


@shared_task(
    bind=True,
    max_retries=2,
    queue="ai_processing",
    name="ai_engine.analyze_user_behavior",
)
def analyze_user_behavior(self, user_id: str):
    """
    Full behavior analysis. Updates user profile with discovered patterns.
    Runs periodically and on event threshold.
    """
    try:
        from apps.habits.models import BehaviorEvent, HabitLog
        from apps.users.models import UserProfile
        from apps.ai_engine.orchestrator import LLMClient
        from apps.ai_engine.prompts import PromptBuilder
        from django.utils import timezone as tz
        from django.db.models import Count

        # Aggregate event data
        now = tz.now()
        cutoff = now - tz.timedelta(days=30)

        events_by_hour = (
            BehaviorEvent.objects.filter(user_id=user_id, occurred_at__gte=cutoff)
            .values("hour_of_day")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        habit_completion = HabitLog.objects.filter(
            user_id=user_id,
            log_date__gte=cutoff.date(),
        ).count()

        summary = f"Peak activity hours: {[e['hour_of_day'] for e in events_by_hour]}\n"
        summary += f"Habit completions (30d): {habit_completion}\n"

        llm = LLMClient()
        builder = PromptBuilder()
        response = llm.complete(
            builder.build_behavior_analysis_prompt(summary),
            max_tokens=500,
            temperature=0.1,
        )

        raw = response["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        analysis = json.loads(raw)

        # Update user profile
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        profile.productivity_windows = analysis.get("productive_hours", [])
        profile.behavior_patterns = {
            "habit_consistency_score": analysis.get("habit_consistency_score", 0),
            "top_categories": analysis.get("top_categories", []),
            "summary": analysis.get("behavioral_summary", ""),
            "analyzed_at": now.isoformat(),
        }
        profile.save(update_fields=["productivity_windows", "behavior_patterns", "updated_at"])

        logger.info("Behavior analysis complete", extra={"user_id": user_id})
        return {"status": "success"}

    except Exception as exc:
        logger.exception("Behavior analysis failed", extra={"user_id": user_id})
        raise self.retry(exc=exc)


@shared_task(
    queue="ai_processing",
    name="ai_engine.generate_daily_recommendations",
)
def generate_daily_recommendations():
    """
    Periodic task (runs daily via Celery Beat).
    Generates personalized recommendations for all active users.
    """
    from apps.users.models import User
    from apps.recommendations.models import Recommendation
    from apps.ai_engine.orchestrator import LLMClient, MemoryManager
    from apps.ai_engine.prompts import PromptBuilder

    active_users = User.objects.filter(is_active=True).only("id")
    llm = LLMClient()
    builder = PromptBuilder()

    for user in active_users:
        try:
            mem_mgr = MemoryManager(str(user.id))
            insights = mem_mgr.get_user_insights()
            if not insights:
                continue

            prompt = [
                {
                    "role": "system",
                    "content": "Generate 3 specific, actionable recommendations for this user based on their insights. Return JSON array: [{title, description, category, priority}]",
                },
                {"role": "user", "content": "\n".join(insights[:10])},
            ]

            response = llm.complete(prompt, max_tokens=800, temperature=0.8)
            raw = response["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            recs = json.loads(raw)

            for rec in recs[:3]:
                Recommendation.objects.create(
                    user=user,
                    title=rec.get("title", "")[:200],
                    description=rec.get("description", ""),
                    category=rec.get("category", "general"),
                    priority=rec.get("priority", "medium"),
                )

        except Exception:
            logger.exception("Daily recommendation failed", extra={"user_id": str(user.id)})

    return {"status": "complete"}


def _extract_topics(text: str) -> list[str]:
    """Simple keyword extraction from summary text."""
    import re
    stopwords = {"the", "a", "an", "is", "are", "was", "were", "and", "or", "but",
                 "in", "on", "at", "to", "for", "of", "with", "about", "this", "that"}
    words = re.findall(r"\b[a-z]{4,}\b", text.lower())
    seen = set()
    topics = []
    for w in words:
        if w not in stopwords and w not in seen:
            seen.add(w)
            topics.append(w)
        if len(topics) >= 5:
            break
    return topics


# Import goal extraction task
from apps.ai_engine.tasks_goals import extract_goals_from_conversation  # noqa: F401, E402

# Import periodic tasks so Celery autodiscover finds them
from apps.ai_engine.tasks_periodic import (  # noqa: F401, E402
    purge_old_behavior_events,
    run_weekly_behavior_analysis,
    create_daily_snapshots,
)
