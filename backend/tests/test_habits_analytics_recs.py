"""
AIU — Habits, Analytics, Recommendations: Tests
"""

from datetime import date, timedelta
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="habits_test@aiu.dev", password="TestPassword123!"
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


# ── Habits ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHabits:
    def test_create_habit(self, auth_client):
        resp = auth_client.post("/api/v1/habits/", {
            "name": "Morning meditation",
            "category": "mindfulness",
        }, format="json")
        assert resp.status_code == 201
        assert resp.json()["current_streak"] == 0

    def test_log_starts_streak(self, auth_client):
        habit = auth_client.post("/api/v1/habits/",
            {"name": "Exercise", "category": "health"}, format="json").json()
        log_resp = auth_client.post(f"/api/v1/habits/{habit['id']}/log/", {})
        assert log_resp.status_code == 200
        assert log_resp.json()["current_streak"] == 1
        assert log_resp.json()["created"] is True

    def test_today_endpoint(self, auth_client):
        auth_client.post("/api/v1/habits/",
            {"name": "Read", "category": "learning"}, format="json")
        resp = auth_client.get("/api/v1/habits/today/")
        assert resp.status_code == 200
        assert "results" in resp.json()

    def test_history_endpoint(self, auth_client):
        habit = auth_client.post("/api/v1/habits/",
            {"name": "Walk", "category": "health"}, format="json").json()
        resp = auth_client.get(f"/api/v1/habits/{habit['id']}/history/?days=7")
        assert resp.status_code == 200
        assert "logs" in resp.json()

    def test_delete_habit(self, auth_client):
        habit = auth_client.post("/api/v1/habits/",
            {"name": "Temp habit", "category": "other"}, format="json").json()
        resp = auth_client.delete(f"/api/v1/habits/{habit['id']}/")
        assert resp.status_code == 204

    def test_streak_continues_on_consecutive_days(self, auth_client, user):
        from apps.habits.models import Habit, HabitLog
        habit = Habit.objects.create(user=user, name="Daily habit", category="other")
        yesterday = date.today() - timedelta(days=1)
        HabitLog.objects.create(habit=habit, user=user, log_date=yesterday)
        habit.current_streak = 1
        habit.save()

        resp = auth_client.post(f"/api/v1/habits/{habit.id}/log/", {})
        assert resp.json()["current_streak"] == 2

    def test_streak_resets_if_day_skipped(self, auth_client, user):
        from apps.habits.models import Habit, HabitLog
        habit = Habit.objects.create(user=user, name="Inconsistent", category="other")
        two_days_ago = date.today() - timedelta(days=2)
        HabitLog.objects.create(habit=habit, user=user, log_date=two_days_ago)
        habit.current_streak = 5
        habit.save()

        resp = auth_client.post(f"/api/v1/habits/{habit.id}/log/", {})
        assert resp.json()["current_streak"] == 1  # Reset to 1


# ── Analytics ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAnalytics:
    def test_dashboard_returns_all_sections(self, auth_client):
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

    def test_behavior_timeline_max_days(self, auth_client):
        # days param max is 90
        resp = auth_client.get("/api/v1/analytics/behavior/?days=200")
        assert resp.status_code == 200  # Should not error, just cap at 90


# ── Recommendations ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRecommendations:
    def test_list_recommendations_empty(self, auth_client):
        resp = auth_client.get("/api/v1/recommendations/")
        assert resp.status_code == 200

    def test_accept_recommendation(self, auth_client, user):
        from apps.recommendations.models import Recommendation
        rec = Recommendation.objects.create(
            user=user,
            title="Try morning journaling",
            description="5 minutes daily journaling improves clarity.",
            category="mindfulness",
            priority="medium",
        )
        resp = auth_client.patch(f"/api/v1/recommendations/{rec.id}/accept/")
        assert resp.status_code == 200
        assert resp.json()["recommendation"]["status"] == "accepted"

    def test_dismiss_recommendation(self, auth_client, user):
        from apps.recommendations.models import Recommendation
        rec = Recommendation.objects.create(
            user=user, title="Walk 10k steps",
            description="Daily walking target", category="health", priority="low",
        )
        resp = auth_client.patch(f"/api/v1/recommendations/{rec.id}/dismiss/")
        assert resp.status_code == 200

    def test_filter_by_status(self, auth_client, user):
        from apps.recommendations.models import Recommendation
        Recommendation.objects.create(user=user, title="Pending rec", description="…",
            category="other", priority="low", status="pending")
        Recommendation.objects.create(user=user, title="Accepted rec", description="…",
            category="other", priority="low", status="accepted")
        resp = auth_client.get("/api/v1/recommendations/?status=pending")
        results = resp.json()["results"]
        assert all(r["status"] == "pending" for r in results)
