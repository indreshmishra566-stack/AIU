"""
AIU — Habits App: Views
CRUD for habits, daily logging, streak management, analytics.
"""

import logging
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Habit, HabitLog, BehaviorEvent

logger = logging.getLogger("apps.habits")


# ── Serializers ───────────────────────────────────────────────────────────────

class HabitSerializer(serializers.ModelSerializer):
    completion_rate_7d = serializers.SerializerMethodField()

    class Meta:
        model = Habit
        fields = [
            "id",
            "name",
            "description",
            "category",
            "frequency",
            "target_count",
            "current_streak",
            "longest_streak",
            "total_completions",
            "is_active",
            "started_on",
            "reminder_time",
            "completion_rate_7d",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "current_streak",
            "longest_streak",
            "total_completions",
            "completion_rate_7d",
            "created_at",
        ]

    def get_completion_rate_7d(self, obj) -> float:
        cutoff = date.today() - timedelta(days=7)
        logs = obj.logs.filter(log_date__gte=cutoff).count()
        return round(logs / 7 * 100, 1)


class HabitLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitLog
        fields = [
            "id",
            "habit",
            "log_date",
            "completed_count",
            "notes",
            "mood_rating",
            "difficulty_rating",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_log_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("Cannot log a future date.")
        return value


# ── Viewsets ──────────────────────────────────────────────────────────────────

class HabitViewSet(ModelViewSet):
    """
    Full CRUD for habits + custom actions: log, streak-summary, today's status.
    """

    serializer_class = HabitSerializer

    def get_queryset(self):
        return (
            Habit.objects.filter(user=self.request.user)
            .prefetch_related("logs")
            .order_by("-is_active", "name")
        )

    def perform_create(self, serializer):
        habit = serializer.save(user=self.request.user)
        logger.info("Habit created", extra={"habit_id": str(habit.id), "user": str(self.request.user.id)})

    @action(detail=True, methods=["post"], url_path="log")
    def log(self, request, pk=None):
        """POST /habits/{id}/log/ — mark today as complete."""
        habit = self.get_object()
        log_date = request.data.get("log_date", str(date.today()))
        notes = request.data.get("notes", "")
        mood = request.data.get("mood_rating")
        difficulty = request.data.get("difficulty_rating")

        try:
            log_date_obj = date.fromisoformat(log_date)
        except ValueError:
            return Response({"status": "error", "message": "Invalid date format."}, status=400)

        if log_date_obj > date.today():
            return Response({"status": "error", "message": "Cannot log future dates."}, status=400)

        with transaction.atomic():
            habit_log, created = HabitLog.objects.get_or_create(
                habit=habit,
                user=request.user,
                log_date=log_date_obj,
                defaults={
                    "notes": notes,
                    "mood_rating": mood,
                    "difficulty_rating": difficulty,
                },
            )

            if created:
                # Update streak counters
                self._update_streak(habit, log_date_obj)
                # Log behavior event
                BehaviorEvent.objects.create(
                    user=request.user,
                    event_type=BehaviorEvent.EventType.HABIT_LOG,
                    payload={"habit_id": str(habit.id), "habit_name": habit.name},
                    hour_of_day=timezone.now().hour,
                    day_of_week=timezone.now().weekday(),
                )

        return Response(
            {
                "status": "success",
                "created": created,
                "current_streak": habit.current_streak,
                "log": HabitLogSerializer(habit_log).data,
            }
        )

    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        """GET /habits/today/ — all habits with today's completion status."""
        habits = self.get_queryset().filter(is_active=True)
        today = date.today()
        completed_ids = set(
            HabitLog.objects.filter(
                user=request.user,
                log_date=today,
                habit__in=habits,
            ).values_list("habit_id", flat=True)
        )

        data = []
        for habit in habits:
            item = HabitSerializer(habit).data
            item["completed_today"] = habit.id in completed_ids
            data.append(item)

        return Response({"status": "success", "results": data, "date": str(today)})

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        """GET /habits/{id}/history/?days=30 — completion history."""
        habit = self.get_object()
        days = min(int(request.query_params.get("days", 30)), 365)
        cutoff = date.today() - timedelta(days=days)
        logs = HabitLog.objects.filter(habit=habit, log_date__gte=cutoff).order_by("log_date")
        return Response(
            {
                "status": "success",
                "habit": HabitSerializer(habit).data,
                "logs": HabitLogSerializer(logs, many=True).data,
            }
        )

    def _update_streak(self, habit: Habit, log_date: date) -> None:
        yesterday = log_date - timedelta(days=1)
        yesterday_logged = HabitLog.objects.filter(habit=habit, log_date=yesterday).exists()

        if yesterday_logged or log_date == habit.started_on:
            habit.current_streak += 1
        else:
            habit.current_streak = 1

        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak

        habit.total_completions += 1
        habit.save(update_fields=["current_streak", "longest_streak", "total_completions"])
