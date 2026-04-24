"""
AIU — Analytics App: Nudge System
Smart nudges based on goals, habits, and behavior patterns.
The Dashboard Action System: Insights → Dashboard → Action
"""

import logging
from datetime import date, timedelta

from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("apps.analytics")


class SmartNudgesView(APIView):
    """
    GET /api/v1/analytics/nudges/
    Returns AI-generated smart nudges based on the user's current state.
    Nudges are the "Action System" layer: converting insights into immediate guidance.
    """

    def get(self, request):
        user = request.user
        nudges = []

        try:
            from apps.goals.models import Goal
            from apps.habits.models import Habit, HabitLog
            from apps.memory.models import MemoryInsight

            today = date.today()

            # ── 1. Overdue goals ─────────────────────────────────────────────
            overdue_goals = Goal.objects.filter(
                user=user,
                status="active",
                target_date__lt=today,
            )[:3]
            for goal in overdue_goals:
                nudges.append({
                    "type":     "warning",
                    "priority": "high",
                    "icon":     "⚠️",
                    "title":    f'Goal overdue: "{goal.title}"',
                    "message":  f"Target date was {goal.target_date}. Update the deadline or break it into smaller steps.",
                    "action":   {"label": "Open goal", "path": f"/goals?id={goal.id}"},
                })

            # ── 2. Stalled goals (no activity in 7+ days) ────────────────────
            week_ago = today - timedelta(days=7)
            stalled_goals = Goal.objects.filter(
                user=user,
                status="active",
            ).exclude(
                activities__occurred_at__date__gte=week_ago,
            )[:2]
            for goal in stalled_goals:
                nudges.append({
                    "type":     "reminder",
                    "priority": "medium",
                    "icon":     "💤",
                    "title":    f'No progress on "{goal.title}"',
                    "message":  "You haven't logged any activity on this goal in 7+ days. Pick one task to do today.",
                    "action":   {"label": "View goal", "path": f"/goals?id={goal.id}"},
                })

            # ── 3. Goals near completion (>= 80% done) ────────────────────────
            near_complete = Goal.objects.filter(
                user=user, status="active", progress_pct__gte=80
            )[:2]
            for goal in near_complete:
                nudges.append({
                    "type":     "encouragement",
                    "priority": "medium",
                    "icon":     "🏁",
                    "title":    f'Almost there: "{goal.title}"',
                    "message":  f"You're {goal.progress_pct}% done. Push through to complete it this week!",
                    "action":   {"label": "Finish goal", "path": f"/goals?id={goal.id}"},
                })

            # ── 4. Habits not logged today ────────────────────────────────────
            active_habits = Habit.objects.filter(user=user, is_active=True)
            logged_today = set(
                HabitLog.objects.filter(user=user, log_date=today)
                .values_list("habit_id", flat=True)
            )
            unlogged = [h for h in active_habits if h.id not in logged_today]
            if len(unlogged) > 0:
                habit_names = ", ".join(h.name for h in unlogged[:3])
                nudges.append({
                    "type":     "reminder",
                    "priority": "low",
                    "icon":     "📋",
                    "title":    "Habits pending today",
                    "message":  f"Still to do: {habit_names}",
                    "action":   {"label": "Log habits", "path": "/habits"},
                })

            # ── 5. Positive streak encouragement ─────────────────────────────
            top_streak = max((h.current_streak for h in active_habits), default=0)
            if top_streak >= 7:
                nudges.append({
                    "type":     "encouragement",
                    "priority": "low",
                    "icon":     "🔥",
                    "title":    f"{top_streak}-day streak!",
                    "message":  "You're on a roll. Keep the momentum going today.",
                    "action":   None,
                })

            # ── 6. New insight available ──────────────────────────────────────
            new_insights = MemoryInsight.objects.filter(
                user=user,
                is_active=True,
                created_at__date__gte=today - timedelta(days=2),
            ).count()
            if new_insights > 0:
                nudges.append({
                    "type":     "info",
                    "priority": "low",
                    "icon":     "🧠",
                    "title":    f"{new_insights} new insight{'s' if new_insights > 1 else ''}",
                    "message":  "AIU has learned something new about you. Check your insights.",
                    "action":   {"label": "View insights", "path": "/insights"},
                })

        except Exception:
            logger.exception("Nudge generation failed", extra={"user_id": str(user.id)})

        # Sort: high → medium → low
        priority_order = {"high": 0, "medium": 1, "low": 2}
        nudges.sort(key=lambda n: priority_order.get(n["priority"], 3))

        return Response({
            "status": "success",
            "nudges": nudges[:5],  # max 5 nudges at a time
        })
