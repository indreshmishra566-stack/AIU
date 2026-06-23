"""
AIU — Habits: Initial Migration
Creates: habits, habit_logs, behavior_events tables.
"""

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Habit",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="habits", to=settings.AUTH_USER_MODEL)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(choices=[("health","Health"),("productivity","Productivity"),("learning","Learning"),("mindfulness","Mindfulness"),("social","Social"),("finance","Finance"),("other","Other")], default="other", max_length=30)),
                ("frequency", models.CharField(choices=[("daily","Daily"),("weekly","Weekly"),("custom","Custom")], default="daily", max_length=20)),
                ("target_count", models.PositiveSmallIntegerField(default=1)),
                ("target_days", models.JSONField(blank=True, default=list)),
                ("current_streak", models.PositiveIntegerField(default=0)),
                ("longest_streak", models.PositiveIntegerField(default=0)),
                ("total_completions", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("started_on", models.DateField(default=django.utils.timezone.now)),
                ("reminder_time", models.TimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "habits", "ordering": ["-is_active", "name"]},
        ),
        migrations.AddIndex(
            model_name="habit",
            index=models.Index(fields=["user", "is_active", "category"], name="habit_user_active_cat_idx"),
        ),
        migrations.CreateModel(
            name="HabitLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("habit", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="logs", to="habits.habit")),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ("log_date", models.DateField(db_index=True)),
                ("completed_count", models.PositiveSmallIntegerField(default=1)),
                ("notes", models.TextField(blank=True)),
                ("mood_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("difficulty_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "habit_logs", "unique_together": {("habit", "log_date")}},
        ),
        migrations.AddIndex(
            model_name="habitlog",
            index=models.Index(fields=["user", "log_date"], name="habitlog_user_date_idx"),
        ),
        migrations.AddIndex(
            model_name="habitlog",
            index=models.Index(fields=["habit", "-log_date"], name="habitlog_habit_date_idx"),
        ),
        migrations.CreateModel(
            name="BehaviorEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ("event_type", models.CharField(choices=[("ai_query","AI Query"),("habit_log","Habit Log"),("habit_skip","Habit Skip"),("goal_set","Goal Set"),("goal_complete","Goal Complete"),("session_start","Session Start"),("session_end","Session End"),("decision_request","Decision Request"),("reflection","Reflection")], db_index=True, max_length=30)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("session_id", models.UUIDField(blank=True, null=True)),
                ("hour_of_day", models.PositiveSmallIntegerField()),
                ("day_of_week", models.PositiveSmallIntegerField()),
                ("occurred_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={"db_table": "behavior_events"},
        ),
        migrations.AddIndex(
            model_name="behaviorevent",
            index=models.Index(fields=["user", "event_type", "-occurred_at"], name="event_user_type_time_idx"),
        ),
        migrations.AddIndex(
            model_name="behaviorevent",
            index=models.Index(fields=["user", "hour_of_day", "day_of_week"], name="event_user_hour_day_idx"),
        ),
    ]
