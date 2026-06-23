"""
AIU — Goals: Initial Migration
Creates: goals, goal_milestones, goal_tasks, goal_activities tables.
"""

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = [("users", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Goal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="goals", to=settings.AUTH_USER_MODEL)),
                ("title", models.CharField(max_length=300)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(choices=[("health","Health & Fitness"),("career","Career & Work"),("learning","Learning & Skills"),("finance","Finance"),("mindfulness","Mindfulness"),("social","Relationships"),("creative","Creative"),("other","Other")], default="other", max_length=30)),
                ("priority", models.CharField(choices=[("low","Low"),("medium","Medium"),("high","High")], default="medium", max_length=10)),
                ("status", models.CharField(choices=[("active","Active"),("paused","Paused"),("completed","Completed"),("abandoned","Abandoned")], db_index=True, default="active", max_length=20)),
                ("progress_pct", models.PositiveSmallIntegerField(default=0)),
                ("target_date", models.DateField(blank=True, null=True)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("ai_recommendation", models.TextField(blank=True)),
                ("extracted_from_chat", models.BooleanField(default=False)),
                ("source_conversation", models.UUIDField(blank=True, null=True)),
                ("current_streak", models.PositiveIntegerField(default=0)),
                ("longest_streak", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "goals", "ordering": ["-priority", "status", "-created_at"]},
        ),
        migrations.AddIndex(model_name="goal", index=models.Index(fields=["user", "status", "-created_at"], name="goal_user_status_time_idx")),
        migrations.AddIndex(model_name="goal", index=models.Index(fields=["user", "category", "status"], name="goal_user_cat_status_idx")),

        migrations.CreateModel(
            name="Milestone",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("goal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="milestones", to="goals.goal")),
                ("title", models.CharField(max_length=300)),
                ("description", models.TextField(blank=True)),
                ("is_completed", models.BooleanField(db_index=True, default=False)),
                ("order", models.PositiveSmallIntegerField(default=0)),
                ("target_date", models.DateField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "goal_milestones", "ordering": ["order", "created_at"]},
        ),

        migrations.CreateModel(
            name="GoalTask",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("goal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="goals.goal")),
                ("milestone", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tasks", to="goals.milestone")),
                ("title", models.CharField(max_length=300)),
                ("status", models.CharField(choices=[("todo","To Do"),("in_progress","In Progress"),("done","Done"),("skipped","Skipped")], db_index=True, default="todo", max_length=20)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "goal_tasks", "ordering": ["status", "due_date", "created_at"]},
        ),

        migrations.CreateModel(
            name="GoalActivity",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("goal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="goals.goal")),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ("activity_type", models.CharField(choices=[("task_done","Task completed"),("milestone_hit","Milestone reached"),("progress_update","Progress updated"),("note_added","Note added"),("ai_suggestion","AI suggestion received"),("status_change","Status changed")], max_length=30)),
                ("description", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={"db_table": "goal_activities", "ordering": ["-occurred_at"]},
        ),
        migrations.AddIndex(model_name="goalactivity", index=models.Index(fields=["goal", "-occurred_at"], name="gact_goal_time_idx")),
        migrations.AddIndex(model_name="goalactivity", index=models.Index(fields=["user", "-occurred_at"], name="gact_user_time_idx")),
    ]
