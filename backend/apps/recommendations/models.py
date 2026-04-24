"""
AIU — Recommendations App: Models + Views
AI-generated personalized recommendations for tasks, habits, and growth.
"""

import uuid
from django.db import models
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action


class Recommendation(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Category(models.TextChoices):
        HABIT = "habit", "Habit"
        SKILL = "skill", "Skill"
        PRODUCTIVITY = "productivity", "Productivity"
        HEALTH = "health", "Health"
        MINDFULNESS = "mindfulness", "Mindfulness"
        GENERAL = "general", "General"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DISMISSED = "dismissed", "Dismissed"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="recommendations", db_index=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.GENERAL)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)

    # AI rationale
    rationale = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.7)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    acted_on_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "recommendations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status", "-created_at"]),
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = [
            "id", "title", "description", "category", "priority",
            "status", "rationale", "confidence_score", "created_at", "acted_on_at",
        ]
        read_only_fields = ["id", "created_at"]


class RecommendationViewSet(ModelViewSet):
    serializer_class = RecommendationSerializer
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        qs = Recommendation.objects.filter(user=self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=["patch"], url_path="accept")
    def accept(self, request, pk=None):
        from django.utils import timezone
        rec = self.get_object()
        rec.status = Recommendation.Status.ACCEPTED
        rec.acted_on_at = timezone.now()
        rec.save(update_fields=["status", "acted_on_at"])
        return Response({"status": "success", "recommendation": RecommendationSerializer(rec).data})

    @action(detail=True, methods=["patch"], url_path="dismiss")
    def dismiss(self, request, pk=None):
        rec = self.get_object()
        rec.status = Recommendation.Status.DISMISSED
        rec.save(update_fields=["status"])
        return Response({"status": "success"})
