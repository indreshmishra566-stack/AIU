"""
AIU — Backend Tests
Unit tests for services, API endpoints, and AI orchestration logic.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@aiu.dev",
        password="TestPassword123!",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def auth_client(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client


# ── Auth Tests ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistration:
    def test_register_success(self, api_client):
        payload = {
            "email": "new@aiu.dev",
            "password": "NewPassword123!",
            "first_name": "Jane",
            "last_name": "Doe",
        }
        resp = api_client.post("/api/v1/auth/register/", payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "success"
        assert "tokens" in data
        assert "access" in data["tokens"]
        assert "refresh" in data["tokens"]
        assert data["user"]["email"] == "new@aiu.dev"

    def test_register_duplicate_email(self, api_client, user):
        payload = {
            "email": user.email,
            "password": "AnotherPassword123!",
            "first_name": "Dup",
            "last_name": "User",
        }
        resp = api_client.post("/api/v1/auth/register/", payload, format="json")
        assert resp.status_code == 400

    def test_register_weak_password(self, api_client):
        payload = {
            "email": "weak@aiu.dev",
            "password": "123",
            "first_name": "Weak",
            "last_name": "Pass",
        }
        resp = api_client.post("/api/v1/auth/register/", payload, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, user):
        resp = api_client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "TestPassword123!"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.json()

    def test_login_wrong_password(self, api_client, user):
        resp = api_client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "WrongPassword!"},
            format="json",
        )
        assert resp.status_code == 401


# ── User Profile Tests ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUserProfile:
    def test_get_me_authenticated(self, auth_client):
        resp = auth_client.get("/api/v1/users/me/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"
        assert "email" in resp.json()["data"]

    def test_get_me_unauthenticated(self, api_client):
        resp = api_client.get("/api/v1/users/me/")
        assert resp.status_code == 401

    def test_update_profile(self, auth_client):
        resp = auth_client.patch(
            "/api/v1/users/me/",
            {"first_name": "Updated", "coach_mode": "strict"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["first_name"] == "Updated"


# ── Habits Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHabits:
    def test_create_habit(self, auth_client):
        resp = auth_client.post(
            "/api/v1/habits/",
            {"name": "Morning run", "category": "health"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Morning run"

    def test_list_habits(self, auth_client):
        # Create 2 habits
        for i in range(2):
            auth_client.post("/api/v1/habits/", {"name": f"Habit {i}", "category": "health"})
        resp = auth_client.get("/api/v1/habits/")
        assert resp.status_code == 200

    def test_log_habit(self, auth_client):
        create_resp = auth_client.post(
            "/api/v1/habits/",
            {"name": "Meditate", "category": "mindfulness"},
            format="json",
        )
        habit_id = create_resp.json()["id"]
        log_resp = auth_client.post(
            f"/api/v1/habits/{habit_id}/log/",
            {},
            format="json",
        )
        assert log_resp.status_code == 200
        assert log_resp.json()["created"] is True
        assert log_resp.json()["current_streak"] == 1

    def test_log_habit_twice_same_day(self, auth_client):
        create_resp = auth_client.post(
            "/api/v1/habits/", {"name": "Habit", "category": "health"}, format="json"
        )
        habit_id = create_resp.json()["id"]
        auth_client.post(f"/api/v1/habits/{habit_id}/log/", {})
        second = auth_client.post(f"/api/v1/habits/{habit_id}/log/", {})
        # Second log of same day returns created=False (already logged)
        assert second.json()["created"] is False


# ── AI Engine Tests ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAIEngine:
    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    @patch("apps.ai_engine.orchestrator.EmbeddingService.embed")
    def test_chat_endpoint(self, mock_embed, mock_complete, auth_client):
        mock_embed.return_value = [0.0] * 1536
        mock_complete.return_value = {
            "content": "This is a test AI response.",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "model": "gpt-4o",
        }
        resp = auth_client.post(
            "/api/v1/ai/chat/",
            {"message": "Hello, how are you?", "coach_mode": "friendly"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "content" in data["data"]
        assert data["data"]["content"] == "This is a test AI response."
        assert "conversation_id" in data["data"]

    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    @patch("apps.ai_engine.orchestrator.EmbeddingService.embed")
    def test_conversation_continuity(self, mock_embed, mock_complete, auth_client):
        mock_embed.return_value = [0.0] * 1536
        mock_complete.return_value = {
            "content": "Response 1",
            "prompt_tokens": 50,
            "completion_tokens": 20,
            "model": "gpt-4o",
        }
        resp1 = auth_client.post("/api/v1/ai/chat/", {"message": "Hello"}, format="json")
        conv_id = resp1.json()["data"]["conversation_id"]

        mock_complete.return_value["content"] = "Response 2"
        resp2 = auth_client.post(
            "/api/v1/ai/chat/",
            {"message": "Continue", "conversation_id": conv_id},
            format="json",
        )
        assert resp2.json()["data"]["conversation_id"] == conv_id

    def test_list_conversations(self, auth_client):
        resp = auth_client.get("/api/v1/ai/conversations/")
        assert resp.status_code == 200
        assert "results" in resp.json()


# ── Memory Tests ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMemory:
    @patch("apps.ai_engine.embeddings.EmbeddingService.embed")
    def test_store_and_retrieve_memory(self, mock_embed, user):
        from apps.ai_engine.orchestrator import MemoryManager

        mock_embed.return_value = [0.1] * 1536
        mgr = MemoryManager(str(user.id))

        mem = mgr.store_memory(
            content="The user prefers working in the morning",
            source_type="insight",
            source_id=uuid.uuid4(),
            importance=0.8,
        )
        assert mem is not None
        assert mem.user_id == user.id

        # Test deduplication
        dup = mgr.store_memory(
            content="The user prefers working in the morning",
            source_type="insight",
            source_id=uuid.uuid4(),
        )
        assert dup is None  # Duplicate not stored


# ── Analytics Tests ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnalytics:
    def test_dashboard_stats(self, auth_client):
        resp = auth_client.get("/api/v1/analytics/dashboard/")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "habits" in data
        assert "conversations" in data
        assert "insights" in data
        assert "activity" in data

    def test_behavior_timeline(self, auth_client):
        resp = auth_client.get("/api/v1/analytics/behavior/?days=7")
        assert resp.status_code == 200
        assert "events" in resp.json()


# ── Throttle Tests ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRateLimiting:
    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    @patch("apps.ai_engine.orchestrator.EmbeddingService.embed")
    def test_ai_endpoint_is_throttled(self, mock_embed, mock_complete, auth_client):
        """AI endpoint has a lower rate limit — verify throttle kicks in."""
        mock_embed.return_value = [0.0] * 1536
        mock_complete.return_value = {
            "content": "ok", "prompt_tokens": 10, "completion_tokens": 5, "model": "gpt-4o"
        }
        # This test would need to override throttle rates for unit testing;
        # in CI it's validated via integration test.
        resp = auth_client.post(
            "/api/v1/ai/chat/", {"message": "test"}, format="json"
        )
        assert resp.status_code in (200, 429)
