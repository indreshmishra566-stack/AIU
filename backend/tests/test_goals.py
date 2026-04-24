"""
AIU — Goals App: Tests
Full test coverage for goal CRUD, milestones, tasks, progress,
AI advice, and activity history.
"""

import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="goals_test@aiu.dev",
        password="TestPassword123!",
        first_name="Goals",
        last_name="Tester",
    )


@pytest.fixture
def auth_client(api_client, user):
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client


@pytest.fixture
def goal(db, user):
    from apps.goals.models import Goal
    return Goal.objects.create(
        user=user,
        title="Learn Django REST Framework",
        description="Master DRF for production APIs",
        category="learning",
        priority="high",
    )


@pytest.mark.django_db
class TestGoalCRUD:
    def test_create_goal(self, auth_client):
        resp = auth_client.post("/api/v1/goals/", {
            "title": "Run a 5K",
            "category": "health",
            "priority": "medium",
        }, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Run a 5K"
        assert data["progress_pct"] == 0
        assert data["status"] == "active"

    def test_create_goal_with_target_date(self, auth_client):
        resp = auth_client.post("/api/v1/goals/", {
            "title": "Read 12 books",
            "category": "learning",
            "target_date": "2025-12-31",
        }, format="json")
        assert resp.status_code == 201
        assert resp.json()["target_date"] == "2025-12-31"

    def test_list_goals(self, auth_client, goal):
        resp = auth_client.get("/api/v1/goals/")
        assert resp.status_code == 200
        assert len(resp.json()["results"]) >= 1

    def test_list_goals_filter_by_status(self, auth_client, goal):
        resp = auth_client.get("/api/v1/goals/?status=active")
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert all(g["status"] == "active" for g in results)

    def test_retrieve_goal(self, auth_client, goal):
        resp = auth_client.get(f"/api/v1/goals/{goal.id}/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == goal.title
        assert "milestones" in data
        assert "milestone_count" in data

    def test_update_goal(self, auth_client, goal):
        resp = auth_client.patch(f"/api/v1/goals/{goal.id}/", {
            "priority": "low",
            "description": "Updated description",
        }, format="json")
        assert resp.status_code == 200
        assert resp.json()["priority"] == "low"

    def test_delete_goal(self, auth_client, goal):
        resp = auth_client.delete(f"/api/v1/goals/{goal.id}/")
        assert resp.status_code == 204

    def test_cannot_access_other_users_goal(self, db, api_client):
        other_user = User.objects.create_user(
            email="other@aiu.dev", password="TestPassword123!"
        )
        from apps.goals.models import Goal
        other_goal = Goal.objects.create(
            user=other_user, title="Private goal", category="other"
        )
        # Auth as first user
        user = User.objects.create_user(email="first@aiu.dev", password="TestPassword123!")
        refresh = RefreshToken.for_user(user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        resp = api_client.get(f"/api/v1/goals/{other_goal.id}/")
        assert resp.status_code == 404

    def test_active_goals_endpoint(self, auth_client, goal):
        resp = auth_client.get("/api/v1/goals/active/")
        assert resp.status_code == 200
        assert "results" in resp.json()

    def test_complete_goal(self, auth_client, goal):
        resp = auth_client.post(f"/api/v1/goals/{goal.id}/complete/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["goal"]["status"] == "completed"
        assert data["goal"]["progress_pct"] == 100


@pytest.mark.django_db
class TestMilestones:
    def test_add_milestone(self, auth_client, goal):
        resp = auth_client.post(f"/api/v1/goals/{goal.id}/add-milestone/", {
            "title": "Complete Chapter 1",
            "order": 1,
        }, format="json")
        assert resp.status_code == 201
        assert resp.json()["milestone"]["title"] == "Complete Chapter 1"

    def test_complete_milestone_updates_progress(self, auth_client, goal):
        # Add 2 milestones
        ms1_resp = auth_client.post(f"/api/v1/goals/{goal.id}/add-milestone/",
            {"title": "MS 1", "order": 1}, format="json")
        ms2_resp = auth_client.post(f"/api/v1/goals/{goal.id}/add-milestone/",
            {"title": "MS 2", "order": 2}, format="json")
        ms1_id = ms1_resp.json()["milestone"]["id"]

        # Complete first milestone
        resp = auth_client.post(
            f"/api/v1/goals/{goal.id}/milestones/{ms1_id}/complete/"
        )
        assert resp.status_code == 200
        assert resp.json()["progress_pct"] == 50  # 1/2 complete

    def test_complete_all_milestones_completes_goal(self, auth_client, goal):
        ms_resp = auth_client.post(f"/api/v1/goals/{goal.id}/add-milestone/",
            {"title": "Only milestone", "order": 1}, format="json")
        ms_id = ms_resp.json()["milestone"]["id"]

        resp = auth_client.post(
            f"/api/v1/goals/{goal.id}/milestones/{ms_id}/complete/"
        )
        assert resp.json()["progress_pct"] == 100
        assert resp.json()["goal_status"] == "completed"


@pytest.mark.django_db
class TestGoalTasks:
    def test_add_task(self, auth_client, goal):
        resp = auth_client.post(f"/api/v1/goals/{goal.id}/add-task/", {
            "title": "Read documentation",
        }, format="json")
        assert resp.status_code == 201
        assert resp.json()["task"]["status"] == "todo"

    def test_complete_task(self, auth_client, goal):
        task_resp = auth_client.post(f"/api/v1/goals/{goal.id}/add-task/",
            {"title": "Do the thing"}, format="json")
        task_id = task_resp.json()["task"]["id"]

        resp = auth_client.post(f"/api/v1/goals/{goal.id}/tasks/{task_id}/complete/")
        assert resp.status_code == 200

        # Verify task is done
        goal_resp = auth_client.get(f"/api/v1/goals/{goal.id}/")
        tasks = goal_resp.json().get("tasks", [])
        done = [t for t in tasks if t["id"] == task_id and t["status"] == "done"]
        assert len(done) == 1


@pytest.mark.django_db
class TestGoalActivity:
    def test_activity_history(self, auth_client, goal):
        resp = auth_client.get(f"/api/v1/goals/{goal.id}/activity/")
        assert resp.status_code == 200
        activities = resp.json()["activities"]
        # Goal creation always logs one activity
        assert len(activities) >= 1
        assert activities[0]["activity_type"] == "status_change"

    def test_activity_logged_on_milestone_complete(self, auth_client, goal):
        ms_resp = auth_client.post(f"/api/v1/goals/{goal.id}/add-milestone/",
            {"title": "Test MS"}, format="json")
        ms_id = ms_resp.json()["milestone"]["id"]
        auth_client.post(f"/api/v1/goals/{goal.id}/milestones/{ms_id}/complete/")

        resp = auth_client.get(f"/api/v1/goals/{goal.id}/activity/")
        types = [a["activity_type"] for a in resp.json()["activities"]]
        assert "milestone_hit" in types


@pytest.mark.django_db
class TestGoalAIAdvice:
    @patch("apps.ai_engine.orchestrator.LLMClient.complete")
    @patch("apps.ai_engine.orchestrator.EmbeddingService.embed")
    def test_ai_advice_endpoint(self, mock_embed, mock_complete, auth_client, goal):
        mock_embed.return_value = [0.0] * 1536
        mock_complete.return_value = {
            "content": "Focus on breaking your goal into daily 30-minute sessions.",
            "prompt_tokens": 80,
            "completion_tokens": 40,
            "model": "gpt-4o",
        }
        resp = auth_client.post(f"/api/v1/goals/{goal.id}/ai-advice/")
        assert resp.status_code == 200
        assert "advice" in resp.json()
        assert len(resp.json()["advice"]) > 0

        # Verify saved to goal
        goal_resp = auth_client.get(f"/api/v1/goals/{goal.id}/")
        assert goal_resp.json()["ai_recommendation"] != ""
