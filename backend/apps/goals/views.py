"""
AIU — Goals App: Views
Full CRUD for goals + milestones + tasks + activity history.
Includes AI recommendation endpoint per goal.
"""

import logging
from datetime import date

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Goal, GoalActivity, GoalTask, Milestone

logger = logging.getLogger("apps.goals")


# ── Serializers ───────────────────────────────────────────────────────────────

class GoalTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model  = GoalTask
        fields = ["id", "title", "status", "due_date", "notes", "completed_at", "created_at"]
        read_only_fields = ["id", "completed_at", "created_at"]


class MilestoneSerializer(serializers.ModelSerializer):
    tasks = GoalTaskSerializer(many=True, read_only=True)

    class Meta:
        model  = Milestone
        fields = ["id", "title", "description", "is_completed", "order",
                  "target_date", "completed_at", "created_at", "tasks"]
        read_only_fields = ["id", "completed_at", "created_at"]


class GoalActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model  = GoalActivity
        fields = ["id", "activity_type", "description", "metadata", "occurred_at"]


class GoalSerializer(serializers.ModelSerializer):
    milestones     = MilestoneSerializer(many=True, read_only=True)
    milestone_count = serializers.SerializerMethodField()
    task_count      = serializers.SerializerMethodField()
    days_remaining  = serializers.SerializerMethodField()

    class Meta:
        model  = Goal
        fields = [
            "id", "title", "description", "category", "priority", "status",
            "progress_pct", "target_date", "started_at", "completed_at",
            "ai_recommendation", "extracted_from_chat",
            "current_streak", "longest_streak",
            "milestones", "milestone_count", "task_count", "days_remaining",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "progress_pct", "ai_recommendation", "extracted_from_chat",
            "current_streak", "longest_streak", "started_at", "completed_at",
            "created_at", "updated_at",
        ]

    def get_milestone_count(self, obj) -> dict:
        total     = obj.milestones.count()
        completed = obj.milestones.filter(is_completed=True).count()
        return {"total": total, "completed": completed}

    def get_task_count(self, obj) -> dict:
        total = obj.tasks.count()
        done  = obj.tasks.filter(status=GoalTask.Status.DONE).count()
        return {"total": total, "done": done}

    def get_days_remaining(self, obj) -> int | None:
        if obj.target_date:
            delta = obj.target_date - date.today()
            return delta.days
        return None


class GoalSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for dashboard/list views (no nested milestones)."""
    milestone_count = serializers.SerializerMethodField()

    class Meta:
        model  = Goal
        fields = [
            "id", "title", "category", "priority", "status",
            "progress_pct", "target_date", "current_streak",
            "ai_recommendation", "milestone_count", "created_at",
        ]

    def get_milestone_count(self, obj) -> dict:
        total     = obj.milestones.count()
        completed = obj.milestones.filter(is_completed=True).count()
        return {"total": total, "completed": completed}


# ── ViewSets ──────────────────────────────────────────────────────────────────

class GoalViewSet(ModelViewSet):
    """
    Full CRUD + custom actions:
    - POST   /goals/{id}/add-milestone/
    - POST   /goals/{id}/add-task/
    - POST   /goals/{id}/complete/
    - GET    /goals/{id}/activity/
    - POST   /goals/{id}/ai-advice/
    - GET    /goals/active/       (dashboard snapshot)
    """

    def get_serializer_class(self):
        if self.action == "list":
            return GoalSummarySerializer
        return GoalSerializer

    def get_queryset(self):
        qs = Goal.objects.filter(user=self.request.user).prefetch_related(
            "milestones", "milestones__tasks", "tasks"
        )
        status_filter = self.request.query_params.get("status")
        category      = self.request.query_params.get("category")
        if status_filter:
            qs = qs.filter(status=status_filter)
        if category:
            qs = qs.filter(category=category)
        return qs

    def perform_create(self, serializer):
        goal = serializer.save(user=self.request.user)
        GoalActivity.objects.create(
            goal=goal, user=self.request.user,
            activity_type=GoalActivity.ActivityType.STATUS_CHANGE,
            description=f'Goal "{goal.title}" created.',
        )
        logger.info("Goal created", extra={"goal_id": str(goal.id), "user": str(self.request.user.id)})

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        goal = serializer.save()
        if goal.status != old_status:
            GoalActivity.objects.create(
                goal=goal, user=self.request.user,
                activity_type=GoalActivity.ActivityType.STATUS_CHANGE,
                description=f'Status changed from {old_status} to {goal.status}.',
            )

    # ── Active goals snapshot (for Dashboard) ─────────────────────────────────
    @action(detail=False, methods=["get"], url_path="active")
    def active(self, request):
        goals = self.get_queryset().filter(status=Goal.Status.ACTIVE)[:5]
        return Response({
            "status":  "success",
            "results": GoalSummarySerializer(goals, many=True).data,
        })

    # ── Add milestone ─────────────────────────────────────────────────────────
    @action(detail=True, methods=["post"], url_path="add-milestone")
    def add_milestone(self, request, pk=None):
        goal = self.get_object()
        serializer = MilestoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        milestone = serializer.save(goal=goal)
        GoalActivity.objects.create(
            goal=goal, user=request.user,
            activity_type=GoalActivity.ActivityType.NOTE_ADDED,
            description=f'Milestone added: "{milestone.title}".',
        )
        return Response({"status": "success", "milestone": MilestoneSerializer(milestone).data},
                        status=status.HTTP_201_CREATED)

    # ── Complete milestone ─────────────────────────────────────────────────────
    @action(detail=True, methods=["post"], url_path="milestones/(?P<milestone_id>[^/.]+)/complete")
    def complete_milestone(self, request, pk=None, milestone_id=None):
        goal = self.get_object()
        try:
            milestone = Milestone.objects.get(id=milestone_id, goal=goal)
        except Milestone.DoesNotExist:
            return Response({"status": "error", "message": "Milestone not found."}, status=404)

        with transaction.atomic():
            milestone.is_completed = True
            milestone.completed_at = timezone.now()
            milestone.save(update_fields=["is_completed", "completed_at"])
            goal.recalculate_progress()

            # Check if goal is complete
            if goal.progress_pct == 100:
                goal.status = Goal.Status.COMPLETED
                goal.completed_at = timezone.now()
                goal.save(update_fields=["status", "completed_at"])

            GoalActivity.objects.create(
                goal=goal, user=request.user,
                activity_type=GoalActivity.ActivityType.MILESTONE_HIT,
                description=f'Milestone completed: "{milestone.title}".',
                metadata={"milestone_id": str(milestone.id), "progress_pct": goal.progress_pct},
            )

        return Response({
            "status":       "success",
            "progress_pct": goal.progress_pct,
            "goal_status":  goal.status,
        })

    # ── Add task ──────────────────────────────────────────────────────────────
    @action(detail=True, methods=["post"], url_path="add-task")
    def add_task(self, request, pk=None):
        goal = self.get_object()
        serializer = GoalTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(goal=goal)
        return Response({"status": "success", "task": GoalTaskSerializer(task).data},
                        status=status.HTTP_201_CREATED)

    # ── Complete task ─────────────────────────────────────────────────────────
    @action(detail=True, methods=["post"], url_path="tasks/(?P<task_id>[^/.]+)/complete")
    def complete_task(self, request, pk=None, task_id=None):
        goal = self.get_object()
        try:
            task = GoalTask.objects.get(id=task_id, goal=goal)
        except GoalTask.DoesNotExist:
            return Response({"status": "error", "message": "Task not found."}, status=404)

        task.status       = GoalTask.Status.DONE
        task.completed_at = timezone.now()
        task.save(update_fields=["status", "completed_at"])

        GoalActivity.objects.create(
            goal=goal, user=request.user,
            activity_type=GoalActivity.ActivityType.TASK_DONE,
            description=f'Task completed: "{task.title}".',
        )
        return Response({"status": "success"})

    # ── Activity history ──────────────────────────────────────────────────────
    @action(detail=True, methods=["get"], url_path="activity")
    def activity(self, request, pk=None):
        goal       = self.get_object()
        activities = goal.activities.order_by("-occurred_at")[:50]
        return Response({
            "status":     "success",
            "activities": GoalActivitySerializer(activities, many=True).data,
        })

    # ── AI Advice for this goal ───────────────────────────────────────────────
    @action(detail=True, methods=["post"], url_path="ai-advice")
    def ai_advice(self, request, pk=None):
        """
        Ask the AI for personalised advice on this specific goal.
        Stores the response as ai_recommendation on the goal.
        """
        goal = self.get_object()
        from apps.ai_engine.orchestrator import AIRequest, orchestrator

        # Build a targeted prompt
        milestone_titles = list(goal.milestones.values_list("title", flat=True)[:5])
        message = (
            f"Give me specific, actionable advice for my goal: '{goal.title}'. "
            f"Current progress: {goal.progress_pct}%. "
            f"Category: {goal.category}. Priority: {goal.priority}. "
            + (f"Milestones: {', '.join(milestone_titles)}." if milestone_titles else "")
            + " What are the top 3 things I should do this week?"
        )

        req = AIRequest(
            user_id=str(request.user.id),
            message=message,
            coach_mode=request.user.profile.coach_mode if hasattr(request.user, "profile") else "friendly",
            extra_context={"goal_id": str(goal.id), "goal_title": goal.title},
        )
        ai_resp = orchestrator.process(req)

        # Save advice to goal
        Goal.objects.filter(pk=goal.pk).update(ai_recommendation=ai_resp.content)
        GoalActivity.objects.create(
            goal=goal, user=request.user,
            activity_type=GoalActivity.ActivityType.AI_SUGGESTION,
            description="AI advice generated.",
            metadata={"tokens": ai_resp.tokens_used},
        )

        return Response({"status": "success", "advice": ai_resp.content})

    # ── Complete goal ─────────────────────────────────────────────────────────
    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        goal = self.get_object()
        goal.status       = Goal.Status.COMPLETED
        goal.progress_pct = 100
        goal.completed_at = timezone.now()
        goal.save(update_fields=["status", "progress_pct", "completed_at"])
        GoalActivity.objects.create(
            goal=goal, user=request.user,
            activity_type=GoalActivity.ActivityType.STATUS_CHANGE,
            description=f'Goal "{goal.title}" marked as completed! 🎉',
        )
        return Response({"status": "success", "goal": GoalSummarySerializer(goal).data})
