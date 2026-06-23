"""
AIU — AI Engine: Goal Extraction Task
Automatically extracts goals from conversations and creates
Goal records, completing the Chat → Goals → Insights → Dashboard flow.
"""

import json
import logging

from celery import shared_task

logger = logging.getLogger("ai_engine")


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    queue="ai_processing",
    name="ai_engine.extract_goals_from_conversation",
)
def extract_goals_from_conversation(self, conversation_id: str, user_id: str):
    """
    Scan a conversation for goal statements and automatically create
    Goal records linked back to the source conversation.

    Examples of what triggers goal extraction:
      - "I want to learn Python"
      - "My goal is to run a marathon"
      - "I'm trying to save $5000 this year"
      - "I need to get fit by summer"
    """
    try:
        from apps.memory.models import Conversation, Message
        from apps.goals.models import Goal, GoalActivity
        from apps.ai_engine.orchestrator import LLMClient
        from apps.users.models import User

        conversation = Conversation.objects.select_related("user").get(
            id=conversation_id, user_id=user_id
        )
        messages = Message.objects.filter(
            conversation=conversation,
            role="user",
        ).order_by("created_at")

        if messages.count() < 2:
            return {"status": "skipped", "reason": "too_few_messages"}

        # Build user message text
        user_text = "\n".join(m.content for m in messages)

        llm = LLMClient()
        prompt = [
            {
                "role": "system",
                "content": """Extract explicit goals from the user's messages.
A goal is something the user WANTS to achieve, PLANS to do, or is TRYING to accomplish.

Return a JSON array of goals (max 3, only high-confidence ones):
[{
  "title": "Short goal title (max 10 words)",
  "description": "What they want to achieve",
  "category": "health|career|learning|finance|mindfulness|social|creative|other",
  "confidence": 0.0-1.0
}]

If no clear goals are present, return an empty array [].
Only extract goals with confidence >= 0.7.
Return ONLY valid JSON, nothing else.""",
            },
            {"role": "user", "content": user_text},
        ]

        response = llm.complete(prompt, max_tokens=600, temperature=0.1)
        raw = response["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        goals_data = json.loads(raw)
        user = conversation.user
        created_count = 0

        for item in goals_data:
            if item.get("confidence", 0) < 0.7:
                continue

            # Avoid creating duplicate goals
            existing = Goal.objects.filter(
                user=user,
                title__iexact=item["title"],
                status__in=["active", "paused"],
            ).exists()
            if existing:
                continue

            goal = Goal.objects.create(
                user=user,
                title=item["title"][:300],
                description=item.get("description", ""),
                category=item.get("category", "other"),
                priority="medium",
                extracted_from_chat=True,
                source_conversation=conversation_id,
            )
            GoalActivity.objects.create(
                goal=goal,
                user=user,
                activity_type=GoalActivity.ActivityType.STATUS_CHANGE,
                description=f'Goal auto-extracted from chat: "{goal.title}".',
                metadata={"source_conversation": str(conversation_id)},
            )
            created_count += 1

        logger.info(
            "Goals extracted from chat",
            extra={
                "conversation_id": conversation_id,
                "goals_created": created_count,
                "user_id": user_id,
            },
        )
        return {"status": "success", "goals_created": created_count}

    except json.JSONDecodeError:
        logger.warning("Goal extraction returned invalid JSON", extra={"conversation_id": conversation_id})
        return {"status": "skipped", "reason": "invalid_json"}
    except Exception as exc:
        logger.exception("Goal extraction failed", extra={"conversation_id": conversation_id})
        raise self.retry(exc=exc)


# Re-export so Celery autodiscover finds this
from apps.goals.models import Goal  # noqa: E402, F401 — needed for import side-effects
