"""
AIU — Habits App: Models
Habit definitions, daily logs, streaks, and behavioral event tracking.
"""

import uuid
from django.db import models
from django.utils import timezone


class Habit(models.Model):
    """User-defined habit to track."""

    class Frequency(models.TextChoices):
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        CUSTOM = "custom", "Custom"

    class Category(models.TextChoices):
        HEALTH = "health", "Health"
        PRODUCTIVITY = "productivity", "Productivity"
        LEARNING = "learning", "Learning"
        MINDFULNESS = "mindfulness", "Mindfulness"
        SOCIAL = "social", "Social"
        FINANCE = "finance", "Finance"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="habits",
        db_index=True,
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.DAILY)
    target_count = models.PositiveSmallIntegerField(default=1)  # times per period
    target_days = models.JSONField(default=list, blank=True)    # [0,1,2...] days of week

    # Gamification
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    total_completions = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True, db_index=True)
    started_on = models.DateField(default=timezone.now)
    reminder_time = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "habits"
        ordering = ["-is_active", "name"]
        indexes = [
            models.Index(fields=["user", "is_active", "category"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class HabitLog(models.Model):
    """Daily completion log for a habit."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="logs")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_index=True)

    log_date = models.DateField(db_index=True)
    completed_count = models.PositiveSmallIntegerField(default=1)
    notes = models.TextField(blank=True)
    mood_rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5
    difficulty_rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1-5

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "habit_logs"
        unique_together = [["habit", "log_date"]]
        indexes = [
            models.Index(fields=["user", "log_date"]),
            models.Index(fields=["habit", "-log_date"]),
        ]


class BehaviorEvent(models.Model):
    """
    Raw event log for behavior analysis.
    Every significant user action is recorded here.
    Celery workers aggregate these into behavioral patterns.
    """

    class EventType(models.TextChoices):
        AI_QUERY = "ai_query", "AI Query"
        HABIT_LOG = "habit_log", "Habit Log"
        HABIT_SKIP = "habit_skip", "Habit Skip"
        GOAL_SET = "goal_set", "Goal Set"
        GOAL_COMPLETE = "goal_complete", "Goal Complete"
        SESSION_START = "session_start", "Session Start"
        SESSION_END = "session_end", "Session End"
        DECISION_REQUEST = "decision_request", "Decision Request"
        REFLECTION = "reflection", "Reflection"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, db_index=True)
    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    session_id = models.UUIDField(null=True, blank=True)
    hour_of_day = models.PositiveSmallIntegerField()  # 0-23, denormalized for fast analytics
    day_of_week = models.PositiveSmallIntegerField()  # 0=Mon, 6=Sun

    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "behavior_events"
        indexes = [
            models.Index(fields=["user", "event_type", "-occurred_at"]),
            models.Index(fields=["user", "hour_of_day", "day_of_week"]),
            models.Index(fields=["-occurred_at"]),  # for pruning old events
        ]
