"""
AIU — Memory App: Tests
"""

import uuid
from unittest.mock import patch
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="memory_test@aiu.dev", password="TestPassword123!"
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.mark.django_db
class TestMemoryInsights:
    def test_list_insights_empty(self, auth_client):
        resp = auth_client.get("/api/v1/memory/insights/")
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_list_insights_filtered_by_type(self, auth_client, user):
        from apps.memory.models import MemoryInsight
        MemoryInsight.objects.create(
            user=user, insight_type="behavior",
            content="Active in mornings", confidence=0.85,
        )
        MemoryInsight.objects.create(
            user=user, insight_type="goal",
            content="Wants to learn Python", confidence=0.9,
        )
        resp = auth_client.get("/api/v1/memory/insights/?type=behavior")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["insight_type"] == "behavior"

    def test_insights_ordered_by_confidence(self, auth_client, user):
        from apps.memory.models import MemoryInsight
        for conf in [0.6, 0.9, 0.75]:
            MemoryInsight.objects.create(
                user=user, insight_type="behavior",
                content=f"Insight at {conf}", confidence=conf,
            )
        resp = auth_client.get("/api/v1/memory/insights/")
        results = resp.json()["results"]
        confidences = [r["confidence"] for r in results]
        assert confidences == sorted(confidences, reverse=True)


@pytest.mark.django_db
class TestConversations:
    def test_list_conversations_empty(self, auth_client):
        resp = auth_client.get("/api/v1/ai/conversations/")
        assert resp.status_code == 200

    def test_archive_conversation(self, auth_client, user):
        from apps.memory.models import Conversation
        conv = Conversation.objects.create(user=user, coach_mode="friendly")
        resp = auth_client.delete(f"/api/v1/ai/conversations/{conv.id}/")
        assert resp.status_code == 204
        conv.refresh_from_db()
        assert conv.is_archived is True


@pytest.mark.django_db
class TestEmbeddingDeduplication:
    @patch("apps.ai_engine.embeddings.EmbeddingService.embed")
    def test_duplicate_memory_not_stored(self, mock_embed, user):
        mock_embed.return_value = [0.1] * 1536
        from apps.ai_engine.orchestrator import MemoryManager
        mgr = MemoryManager(str(user.id))

        content = "User prefers morning work sessions"
        mem1 = mgr.store_memory(content, "message", uuid.uuid4())
        mem2 = mgr.store_memory(content, "message", uuid.uuid4())

        assert mem1 is not None
        assert mem2 is None  # Duplicate blocked

    @patch("apps.ai_engine.embeddings.EmbeddingService.embed")
    def test_different_content_both_stored(self, mock_embed, user):
        mock_embed.return_value = [0.2] * 1536
        from apps.ai_engine.orchestrator import MemoryManager
        mgr = MemoryManager(str(user.id))

        mem1 = mgr.store_memory("Content A", "message", uuid.uuid4())
        mock_embed.return_value = [0.3] * 1536
        mem2 = mgr.store_memory("Content B", "message", uuid.uuid4())

        assert mem1 is not None
        assert mem2 is not None
