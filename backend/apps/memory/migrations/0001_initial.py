"""
AIU — Memory: Initial Migration
"""

import django.contrib.postgres.fields
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


def try_create_vector_extension(apps, schema_editor):
    try:
        schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    except Exception:
        pass  # vector extension unavailable on this postgres plan — ok


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(try_create_vector_extension, reverse_code=noop),

        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="conversations", to=settings.AUTH_USER_MODEL)),
                ("title", models.CharField(blank=True, max_length=300)),
                ("summary", models.TextField(blank=True)),
                ("coach_mode", models.CharField(blank=True, max_length=20)),
                ("is_archived", models.BooleanField(db_index=True, default=False)),
                ("topics", django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), blank=True, default=list, size=None)),
                ("sentiment_score", models.FloatField(blank=True, null=True)),
                ("importance_score", models.FloatField(default=0.5)),
                ("started_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "conversations", "ordering": ["-last_message_at"]},
        ),
        migrations.AddIndex(
            model_name="conversation",
            index=models.Index(fields=["user", "is_archived", "-last_message_at"], name="conv_user_arch_time_idx"),
        ),

        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("conversation", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="memory.conversation")),
                ("role", models.CharField(choices=[("user","User"),("assistant","Assistant"),("system","System")], max_length=20)),
                ("content", models.TextField()),
                ("entities", models.JSONField(blank=True, default=dict)),
                ("intent", models.CharField(blank=True, max_length=100)),
                ("sentiment", models.FloatField(blank=True, null=True)),
                ("prompt_tokens", models.PositiveIntegerField(default=0)),
                ("completion_tokens", models.PositiveIntegerField(default=0)),
                ("model_used", models.CharField(blank=True, max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={"db_table": "messages", "ordering": ["created_at"]},
        ),

        migrations.CreateModel(
            name="MemoryEmbedding",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="embeddings", to=settings.AUTH_USER_MODEL)),
                ("source_type", models.CharField(choices=[("message","Message"),("insight","Insight"),("habit","Habit"),("goal","Goal")], db_index=True, max_length=30)),
                ("source_id", models.UUIDField(db_index=True)),
                ("content", models.TextField()),
                ("content_hash", models.CharField(db_index=True, max_length=64)),
                ("embedding_json", models.JSONField(default=list, blank=True)),
                ("importance_score", models.FloatField(db_index=True, default=0.5)),
                ("access_count", models.PositiveIntegerField(default=0)),
                ("last_accessed", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={"db_table": "memory_embeddings"},
        ),
        migrations.AddIndex(
            model_name="memoryembedding",
            index=models.Index(fields=["user", "source_type", "-importance_score"], name="memb_user_src_imp_idx"),
        ),
        migrations.AddIndex(
            model_name="memoryembedding",
            index=models.Index(fields=["user", "content_hash"], name="memb_user_hash_idx"),
        ),

        migrations.CreateModel(
            name="MemoryInsight",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("user", models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name="insights", to=settings.AUTH_USER_MODEL)),
                ("insight_type", models.CharField(choices=[("personality","Personality trait"),("behavior","Behavior pattern"),("preference","Preference"),("goal","Goal"),("skill","Skill"),("challenge","Challenge"),("relationship","Relationship")], db_index=True, max_length=30)),
                ("content", models.TextField()),
                ("confidence", models.FloatField(default=0.7)),
                ("evidence_count", models.PositiveIntegerField(default=1)),
                ("source_conversations", django.contrib.postgres.fields.ArrayField(base_field=models.UUIDField(), blank=True, default=list, size=None)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "memory_insights"},
        ),
        migrations.AddIndex(
            model_name="memoryinsight",
            index=models.Index(fields=["user", "insight_type", "is_active"], name="insight_user_type_active_idx"),
        ),
    ]
