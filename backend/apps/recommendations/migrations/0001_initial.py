"""
AIU — Recommendations: Initial Migration
"""

import django.db.models.deletion
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
            name="Recommendation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="recommendations", to=settings.AUTH_USER_MODEL)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("category", models.CharField(choices=[("habit","Habit"),("skill","Skill"),("productivity","Productivity"),("health","Health"),("mindfulness","Mindfulness"),("general","General")], default="general", max_length=30)),
                ("priority", models.CharField(choices=[("low","Low"),("medium","Medium"),("high","High")], default="medium", max_length=10)),
                ("status", models.CharField(choices=[("pending","Pending"),("accepted","Accepted"),("dismissed","Dismissed"),("completed","Completed")], db_index=True, default="pending", max_length=20)),
                ("rationale", models.TextField(blank=True)),
                ("confidence_score", models.FloatField(default=0.7)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("acted_on_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "recommendations", "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="recommendation",
            index=models.Index(fields=["user", "status", "-created_at"], name="rec_user_status_time_idx"),
        ),
    ]
