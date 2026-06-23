"""
AIU — Analytics App: Serializers
"""
from rest_framework import serializers
from .models import DailySnapshot


class DailySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailySnapshot
        fields = [
            "id", "snapshot_date",
            "habits_completed", "habits_total", "habit_completion_rate",
            "ai_messages_sent", "ai_sessions", "avg_session_sentiment",
            "active_hours", "peak_hour",
        ]
        read_only_fields = fields
