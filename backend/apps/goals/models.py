"""
AIU — Goals App: Models
Structured growth system: Goals → Milestones → Tasks → Progress
This is the core "structured plans" layer of AIU.
"""

import uuid
from django.db import models
from django.utils import timezone


class Goal(models.Model):
    """
    A user-defined goal. Can be extracted from chat automatically
    or created manually. Connected to milestones and tasks.
    """

    class Status(models.TextChoices):
        ACTIVE     = "active",     "Active"
        PAUSED     = "paused",     "Paused"
        COMPLETED  = "completed",  "Completed"
        ABANDONED  = "abandoned",  "Abandoned"

    class Category(models.TextChoices):
        HEALTH      = "health",      "Health & Fitness"
        CAREER      = "career",      "Career & Work"
        LEARNING    = "learning",    "Learning & Skills"
        FINANCE     = "finance",     "Finance"
        MINDFULNESS = "mindfulness", "Mindfulness"
        SOCIAL      = "social",      "Relationships"
        CREATIVE    = "creative",    "Creative"
        OTHER       = "other",       "Other"

    class Priority(models.TextChoices):
        LOW    = "low",    "Low"
        MEDIUM = "medium", "Medium"
        HIGH   = "high",   "High"

    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user     = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="goals", db_index=True
    )

    title       = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    category    = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    priority    = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    # Progress (0-100)
    progress_pct = models.PositiveSmallIntegerField(default=0)

    # Timeline
    target_date = models.DateField(null=True, blank=True)
    started_at  = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    # AI-generated context
    ai_recommendation = models.TextField(blank=True)   # latest AI advice for this goal
    extracted_from_chat = models.BooleanField(default=False)  # auto-extracted vs manual
    source_conversation = models.UUIDField(null=True, blank=True)

    # Streak
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "goals"
        ordering = ["-priority", "status", "-created_at"]
        indexes = [
            models.Index(fields=["user", "status", "-created_at"]),
            models.Index(fields=["user", "category", "status"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.user.email})"

    def recalculate_progress(self):
        """Recalculate progress_pct from milestone/task completion."""
        milestones = self.milestones.all()
        if not milestones.exists():
            return
        completed = milestones.filter(is_completed=True).count()
        total     = milestones.count()
        self.progress_pct = int((completed / total) * 100) if total else 0
        self.save(update_fields=["progress_pct", "updated_at"])


class Milestone(models.Model):
    """
    A measurable checkpoint within a goal.
    Example: Goal = "Learn Python" → Milestone = "Complete Chapter 5"
    """

    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="milestones")

    title        = models.CharField(max_length=300)
    description  = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False, db_index=True)
    order        = models.PositiveSmallIntegerField(default=0)

    target_date  = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "goal_milestones"
        ordering = ["order", "created_at"]


class GoalTask(models.Model):
    """
    A concrete, actionable task under a milestone.
    """

    class Status(models.TextChoices):
        TODO        = "todo",        "To Do"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE        = "done",        "Done"
        SKIPPED     = "skipped",     "Skipped"

    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal      = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="tasks")
    milestone = models.ForeignKey(
        Milestone, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )

    title      = models.CharField(max_length=300)
    status     = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO, db_index=True)
    due_date   = models.DateField(null=True, blank=True)
    notes      = models.TextField(blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "goal_tasks"
        ordering = ["status", "due_date", "created_at"]


class GoalActivity(models.Model):
    """
    Activity history log for a goal.
    Every meaningful action (task completed, milestone hit, note added) is recorded.
    Powers the "Activity history per goal" feature.
    """

    class ActivityType(models.TextChoices):
        TASK_DONE       = "task_done",       "Task completed"
        MILESTONE_HIT   = "milestone_hit",   "Milestone reached"
        PROGRESS_UPDATE = "progress_update", "Progress updated"
        NOTE_ADDED      = "note_added",      "Note added"
        AI_SUGGESTION   = "ai_suggestion",   "AI suggestion received"
        STATUS_CHANGE   = "status_change",   "Status changed"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal         = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name="activities")
    user         = models.ForeignKey("users.User", on_delete=models.CASCADE, db_index=True)
    activity_type = models.CharField(max_length=30, choices=ActivityType.choices)
    description  = models.TextField()
    metadata     = models.JSONField(default=dict, blank=True)
    occurred_at  = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "goal_activities"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["goal", "-occurred_at"]),
            models.Index(fields=["user", "-occurred_at"]),
        ]
