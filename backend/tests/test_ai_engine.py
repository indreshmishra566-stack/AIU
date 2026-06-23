"""
AIU — AI Engine: Tests
Tests for orchestrator, memory, embeddings, goal extraction, Celery tasks.
"""

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="ai_test@aiu.dev", password="TestPassword123!"
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.mark.django_db
class TestAIOrchestrator:
    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    @patch("apps.ai_engine.orchestrator.EmbeddingService.embed")
    def test_process_returns_response(self, mock_embed, mock_complete, user):
        mock_embed.return_value = [0.0] * 1536
        mock_complete.return_value = {
            "content": "Here is my response.",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "model": "gpt-4o",
        }
        from apps.ai_engine.orchestrator import AIRequest, AIOrchestrator
        orch = AIOrchestrator()
        req = AIRequest(user_id=str(user.id), message="Test message", coach_mode="friendly")
        resp = orch.process(req)

        assert resp.content == "Here is my response."
        assert resp.tokens_used == 150
        assert resp.conversation_id is not None

    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    @patch("apps.ai_engine.orchestrator.EmbeddingService.embed")
    def test_conversation_created_on_first_message(self, mock_embed, mock_complete, user):
        mock_embed.return_value = [0.0] * 1536
        mock_complete.return_value = {"content": "Hi", "prompt_tokens": 10, "completion_tokens": 5, "model": "gpt-4o"}
        from apps.ai_engine.orchestrator import AIRequest, AIOrchestrator
        from apps.memory.models import Conversation
        orch = AIOrchestrator()
        req = AIRequest(user_id=str(user.id), message="Hello", coach_mode="mentor")
        resp = orch.process(req)

        conv = Conversation.objects.get(id=resp.conversation_id)
        assert conv.user == user
        assert conv.coach_mode == "mentor"

    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    @patch("apps.ai_engine.orchestrator.EmbeddingService.embed")
    def test_messages_saved_to_conversation(self, mock_embed, mock_complete, user):
        mock_embed.return_value = [0.0] * 1536
        mock_complete.return_value = {"content": "Response", "prompt_tokens": 20, "completion_tokens": 10, "model": "gpt-4o"}
        from apps.ai_engine.orchestrator import AIRequest, AIOrchestrator
        from apps.memory.models import Message
        orch = AIOrchestrator()
        req = AIRequest(user_id=str(user.id), message="What's my plan?")
        resp = orch.process(req)

        msgs = Message.objects.filter(conversation_id=resp.conversation_id)
        assert msgs.count() == 2  # user + assistant
        roles = list(msgs.values_list("role", flat=True))
        assert "user" in roles
        assert "assistant" in roles

    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    @patch("apps.ai_engine.orchestrator.EmbeddingService.embed")
    def test_coach_mode_affects_prompt(self, mock_embed, mock_complete, user):
        mock_embed.return_value = [0.0] * 1536
        captured_messages = []

        def capture_complete(messages, **kwargs):
            captured_messages.extend(messages)
            return {"content": "ok", "prompt_tokens": 10, "completion_tokens": 5, "model": "gpt-4o"}

        mock_complete.side_effect = capture_complete
        from apps.ai_engine.orchestrator import AIRequest, AIOrchestrator
        orch = AIOrchestrator()

        for mode in ["friendly", "strict", "mentor", "analytical"]:
            captured_messages.clear()
            req = AIRequest(user_id=str(user.id), message="Help me", coach_mode=mode)
            orch.process(req)
            system_msg = next(m for m in captured_messages if m["role"] == "system")
            # Each mode has distinctive language in the system prompt
            assert len(system_msg["content"]) > 100


@pytest.mark.django_db
class TestMemoryManager:
    @patch("apps.ai_engine.embeddings.EmbeddingService.embed")
    def test_short_term_memory_roundtrip(self, mock_embed, user):
        mock_embed.return_value = [0.0] * 1536
        from apps.ai_engine.orchestrator import MemoryManager
        mgr = MemoryManager(str(user.id))
        conv_id = str(uuid.uuid4())

        mgr.append_short_term(conv_id, "user", "Hello AI")
        mgr.append_short_term(conv_id, "assistant", "Hello human")

        messages = mgr.get_short_term(conv_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    @patch("apps.ai_engine.embeddings.EmbeddingService.embed")
    def test_short_term_memory_capped(self, mock_embed, user):
        mock_embed.return_value = [0.0] * 1536
        from apps.ai_engine.orchestrator import MemoryManager
        mgr = MemoryManager(str(user.id))
        conv_id = str(uuid.uuid4())

        # Add more than the window size
        for i in range(15):
            mgr.append_short_term(conv_id, "user", f"Message {i}")

        messages = mgr.get_short_term(conv_id)
        assert len(messages) <= 10  # capped at CONTEXT_WINDOW_MESSAGES

    @patch("apps.ai_engine.embeddings.EmbeddingService.embed")
    def test_get_user_insights(self, mock_embed, user):
        mock_embed.return_value = [0.0] * 1536
        from apps.ai_engine.orchestrator import MemoryManager
        from apps.memory.models import MemoryInsight
        MemoryInsight.objects.create(
            user=user, insight_type="behavior",
            content="Productive in the mornings", confidence=0.9,
        )
        mgr = MemoryManager(str(user.id))
        insights = mgr.get_user_insights()
        assert len(insights) == 1
        assert "Productive in the mornings" in insights[0]


@pytest.mark.django_db
class TestGoalExtraction:
    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    def test_goal_extracted_from_chat(self, mock_complete, user):
        mock_complete.return_value = {
            "content": json.dumps([{
                "title": "Learn Python",
                "description": "Master Python programming",
                "category": "learning",
                "confidence": 0.9,
            }]),
            "prompt_tokens": 50,
            "completion_tokens": 30,
            "model": "gpt-4o",
        }
        from apps.memory.models import Conversation, Message
        from apps.ai_engine.tasks_goals import extract_goals_from_conversation
        from apps.goals.models import Goal

        conv = Conversation.objects.create(user=user, coach_mode="friendly")
        Message.objects.create(conversation=conv, role="user", content="I want to learn Python")
        Message.objects.create(conversation=conv, role="user", content="It's my main goal for this year")

        result = extract_goals_from_conversation(str(conv.id), str(user.id))
        assert result["goals_created"] == 1

        goal = Goal.objects.get(user=user, title="Learn Python")
        assert goal.extracted_from_chat is True
        assert str(goal.source_conversation) == str(conv.id)

    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    def test_duplicate_goal_not_created(self, mock_complete, user):
        from apps.goals.models import Goal
        Goal.objects.create(user=user, title="Learn Python", category="learning", status="active")

        mock_complete.return_value = {
            "content": json.dumps([{
                "title": "learn python",
                "description": "Python programming",
                "category": "learning",
                "confidence": 0.85,
            }]),
            "prompt_tokens": 30, "completion_tokens": 20, "model": "gpt-4o",
        }
        from apps.memory.models import Conversation, Message
        from apps.ai_engine.tasks_goals import extract_goals_from_conversation

        conv = Conversation.objects.create(user=user)
        Message.objects.create(conversation=conv, role="user", content="I want to learn python")
        Message.objects.create(conversation=conv, role="user", content="it is my goal")

        result = extract_goals_from_conversation(str(conv.id), str(user.id))
        assert result["goals_created"] == 0  # Duplicate blocked


@pytest.mark.django_db
class TestPromptBuilder:
    def test_build_returns_messages_list(self):
        from apps.ai_engine.prompts import PromptBuilder
        builder = PromptBuilder()
        messages = builder.build(
            user_message="What should I do today?",
            recent_messages=[{"role": "user", "content": "Hello"}],
            retrieved_memories=["User likes mornings"],
            user_insights=["[behavior] Active in mornings"],
            coach_mode="friendly",
        )
        assert isinstance(messages, list)
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "What should I do today?"

    def test_all_coach_modes_produce_different_prompts(self):
        from apps.ai_engine.prompts import PromptBuilder
        builder = PromptBuilder()
        prompts = {}
        for mode in ["friendly", "mentor", "strict", "analytical"]:
            messages = builder.build("test", [], [], [], coach_mode=mode)
            prompts[mode] = messages[0]["content"]
        # All system prompts should be different
        assert len(set(prompts.values())) == 4
