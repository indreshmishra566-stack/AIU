"""
AIU — Analytics App: Models
Lightweight — analytics reads from other apps' tables.
This model stores aggregated daily snapshots for fast dashboard queries.
"""

import uuid
from django.conf import settings
from django.db import models


class DailySnapshot(models.Model):
    """
    Daily aggregated stats per user. Created by a Celery Beat task each midnight.
    Allows fast historical dashboard queries without scanning raw event tables.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_snapshots",
        db_index=True,
    )
    snapshot_date = models.DateField(db_index=True)

    # Habit stats
    habits_completed = models.PositiveSmallIntegerField(default=0)
    habits_total = models.PositiveSmallIntegerField(default=0)
    habit_completion_rate = models.FloatField(default=0.0)

    # AI stats
    ai_messages_sent = models.PositiveSmallIntegerField(default=0)
    ai_sessions = models.PositiveSmallIntegerField(default=0)
    avg_session_sentiment = models.FloatField(default=0.0)

    # Behavior
    active_hours = models.PositiveSmallIntegerField(default=0)
    peak_hour = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "daily_snapshots"
        unique_together = [["user", "snapshot_date"]]
        ordering = ["-snapshot_date"]
        indexes = [
            models.Index(fields=["user", "-snapshot_date"]),
        ]

    def __str__(self):
        return f"Snapshot:{self.user_id}:{self.snapshot_date}"
