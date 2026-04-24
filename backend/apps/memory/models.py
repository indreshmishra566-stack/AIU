"""
AIU — Memory App: Models
"""

import uuid
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="conversations", db_index=True)
    title = models.CharField(max_length=300, blank=True)
    summary = models.TextField(blank=True)
    coach_mode = models.CharField(max_length=20, blank=True)
    is_archived = models.BooleanField(default=False, db_index=True)
    topics = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    importance_score = models.FloatField(default=0.5)
    started_at = models.DateTimeField(auto_now_add=True, db_index=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conversations"
        ordering = ["-last_message_at"]
        indexes = [models.Index(fields=["user", "is_archived", "-last_message_at"])]


class Message(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages", db_index=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    entities = models.JSONField(default=dict, blank=True)
    intent = models.CharField(max_length=100, blank=True)
    sentiment = models.FloatField(null=True, blank=True)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    model_used = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]
        indexes = [models.Index(fields=["conversation", "created_at"])]


class MemoryEmbedding(models.Model):
    """
    Text chunk + embedding stored as JSON list.
    Falls back to importance/recency ranking when vector search unavailable.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="embeddings", db_index=True)
    source_type = models.CharField(max_length=30,
        choices=[("message","Message"),("insight","Insight"),("habit","Habit"),("goal","Goal")],
        db_index=True)
    source_id = models.UUIDField(db_index=True)
    content = models.TextField()
    content_hash = models.CharField(max_length=64, db_index=True)
    embedding_json = models.JSONField(default=list, blank=True)  # list of floats
    importance_score = models.FloatField(default=0.5, db_index=True)
    access_count = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "memory_embeddings"
        indexes = [
            models.Index(fields=["user", "source_type", "-importance_score"]),
            models.Index(fields=["user", "content_hash"]),
        ]


class MemoryInsight(models.Model):
    class InsightType(models.TextChoices):
        PERSONALITY = "personality", "Personality trait"
        BEHAVIOR = "behavior", "Behavior pattern"
        PREFERENCE = "preference", "Preference"
        GOAL = "goal", "Goal"
        SKILL = "skill", "Skill"
        CHALLENGE = "challenge", "Challenge"
        RELATIONSHIP = "relationship", "Relationship"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="insights", db_index=True)
    insight_type = models.CharField(max_length=30, choices=InsightType.choices, db_index=True)
    content = models.TextField()
    confidence = models.FloatField(default=0.7)
    evidence_count = models.PositiveIntegerField(default=1)
    source_conversations = ArrayField(models.UUIDField(), default=list, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "memory_insights"
        indexes = [
            models.Index(fields=["user", "insight_type", "is_active"]),
            models.Index(fields=["user", "-confidence"]),
        ]
