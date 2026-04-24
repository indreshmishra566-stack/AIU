"""
AIU — Memory App: Serializers
Standalone import point for memory serializers.
The serializer classes live in views.py alongside the views that use them;
this module re-exports them for use in other apps (e.g. ai_engine views).
"""

from rest_framework import serializers
from .models import Conversation, Message, MemoryInsight


class ConversationSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model  = Conversation
        fields = [
            "id", "title", "summary", "coach_mode",
            "topics", "sentiment_score", "importance_score",
            "started_at", "last_message_at", "is_archived", "message_count",
        ]

    def get_message_count(self, obj) -> int:
        # Use annotated value if available (avoids N+1)
        return getattr(obj, "message_count_", None) or obj.messages.count()


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Message
        fields = [
            "id", "role", "content", "intent", "sentiment",
            "prompt_tokens", "completion_tokens", "model_used", "created_at",
        ]


class MemoryInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MemoryInsight
        fields = [
            "id", "insight_type", "content", "confidence",
            "evidence_count", "is_active", "created_at", "updated_at",
        ]


__all__ = ["ConversationSerializer", "MessageSerializer", "MemoryInsightSerializer"]
