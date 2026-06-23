"""
AIU — Analytics: Initial Migration
"""

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailySnapshot",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="daily_snapshots", to=settings.AUTH_USER_MODEL)),
                ("snapshot_date", models.DateField(db_index=True)),
                ("habits_completed", models.PositiveSmallIntegerField(default=0)),
                ("habits_total", models.PositiveSmallIntegerField(default=0)),
                ("habit_completion_rate", models.FloatField(default=0.0)),
                ("ai_messages_sent", models.PositiveSmallIntegerField(default=0)),
                ("ai_sessions", models.PositiveSmallIntegerField(default=0)),
                ("avg_session_sentiment", models.FloatField(default=0.0)),
                ("active_hours", models.PositiveSmallIntegerField(default=0)),
                ("peak_hour", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "daily_snapshots", "ordering": ["-snapshot_date"], "unique_together": {("user", "snapshot_date")}},
        ),
        migrations.AddIndex(
            model_name="dailysnapshot",
            index=models.Index(fields=["user", "-snapshot_date"], name="snapshot_user_date_idx"),
        ),
    ]
