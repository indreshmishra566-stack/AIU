"""
AIU — Analytics App: Views
User-level behavioral analytics and insights dashboard data.
"""

from datetime import date, timedelta

from django.db.models import Avg, Count, Max
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.habits.models import BehaviorEvent, Habit, HabitLog
from apps.goals.models import Goal
from apps.memory.models import Conversation, MemoryInsight, Message


class DashboardStatsView(APIView):
    """
    GET /api/v1/analytics/dashboard/
    Returns aggregated stats for the user dashboard.
    """

    def get(self, request):
        user = request.user
        today = date.today()
        last_30 = today - timedelta(days=30)
        last_7 = today - timedelta(days=7)

        # ── Habits ────────────────────────────────────────────────────────────
        active_habits = Habit.objects.filter(user=user, is_active=True)
        completed_today = HabitLog.objects.filter(
            user=user, log_date=today
        ).count()
        habit_completion_30d = HabitLog.objects.filter(
            user=user, log_date__gte=last_30
        ).count()
        top_streak = active_habits.aggregate(top=Max("current_streak"))["top"] or 0

        # ── Conversations ─────────────────────────────────────────────────────
        total_convs = Conversation.objects.filter(user=user).count()
        convs_7d = Conversation.objects.filter(
            user=user, started_at__date__gte=last_7
        ).count()
        total_messages = Message.objects.filter(conversation__user=user).count()
        avg_sentiment = (
            Message.objects.filter(conversation__user=user, sentiment__isnull=False)
            .aggregate(avg=Avg("sentiment"))["avg"]
            or 0.0
        )

        # ── Insights ──────────────────────────────────────────────────────────
        insights_by_type = (
            MemoryInsight.objects.filter(user=user, is_active=True)
            .values("insight_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # ── Activity heatmap (hourly activity past 7 days) ────────────────────
        activity_by_hour = (
            BehaviorEvent.objects.filter(user=user, occurred_at__date__gte=last_7)
            .values("hour_of_day")
            .annotate(count=Count("id"))
            .order_by("hour_of_day")
        )
        heatmap = {str(row["hour_of_day"]): row["count"] for row in activity_by_hour}

        # ── Behavior patterns from profile ────────────────────────────────────
        try:
            profile = user.profile
            behavior = profile.behavior_patterns
            productive_hours = profile.productivity_windows
        except Exception:
            behavior = {}
            productive_hours = []

        return Response(
            {
                "status": "success",
                "data": {
                    "habits": {
                        "active_count": active_habits.count(),
                        "completed_today": completed_today,
                        "completion_30d": habit_completion_30d,
                        "top_streak": top_streak,
                    },
                    "conversations": {
                        "total": total_convs,
                        "last_7_days": convs_7d,
                        "total_messages": total_messages,
                        "avg_sentiment": round(avg_sentiment, 3),
                    },
                    "insights": {
                        "breakdown": list(insights_by_type),
                        "total": sum(i["count"] for i in insights_by_type),
                    },
                    "activity": {
                        "heatmap_by_hour": heatmap,
                        "productive_hours": productive_hours,
                        "behavior_summary": behavior.get("summary", ""),
                        "habit_consistency_score": behavior.get("habit_consistency_score", 0),
                    },
                    "goals": {
                        "active_count":    active_goals,
                        "completed_count": completed_goals,
                        "avg_progress":    avg_progress,
                    },
                },
            }
        )


class BehaviorTimelineView(APIView):
    """
    GET /api/v1/analytics/behavior/?days=7
    Returns raw event timeline for visualization.
    """

    def get(self, request):
        days = min(int(request.query_params.get("days", 7)), 90)
        cutoff = date.today() - timedelta(days=days)

        events = (
            BehaviorEvent.objects.filter(user=request.user, occurred_at__date__gte=cutoff)
            .values("event_type", "occurred_at", "hour_of_day", "day_of_week")
            .order_by("-occurred_at")[:500]
        )

        return Response({"status": "success", "events": list(events)})
