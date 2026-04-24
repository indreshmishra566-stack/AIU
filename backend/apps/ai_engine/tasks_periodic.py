"""
AIU — Additional Celery tasks referenced in celery.py beat schedule.
These complete the full task inventory.
"""

import logging
from celery import shared_task

logger = logging.getLogger("ai_engine")


@shared_task(
    queue="analytics",
    name="ai_engine.purge_old_behavior_events",
)
def purge_old_behavior_events():
    """
    Periodic task: delete behavior events older than 90 days.
    Keeps the table manageable while preserving aggregated snapshots.
    """
    from django.utils import timezone
    from apps.habits.models import BehaviorEvent

    cutoff = timezone.now() - timezone.timedelta(days=90)
    deleted, _ = BehaviorEvent.objects.filter(occurred_at__lt=cutoff).delete()
    logger.info("Purged old behavior events", extra={"deleted_count": deleted})
    return {"status": "success", "deleted": deleted}


@shared_task(
    queue="ai_processing",
    name="ai_engine.run_weekly_behavior_analysis",
)
def run_weekly_behavior_analysis():
    """
    Periodic task: run full behavior analysis for all active users.
    Triggered weekly by Celery Beat.
    """
    from apps.users.models import User
    from apps.ai_engine.tasks import analyze_user_behavior

    active_users = User.objects.filter(is_active=True).values_list("id", flat=True)
    count = 0
    for user_id in active_users:
        analyze_user_behavior.delay(str(user_id))
        count += 1

    logger.info("Weekly behavior analysis dispatched", extra={"user_count": count})
    return {"status": "dispatched", "user_count": count}


@shared_task(
    queue="analytics",
    name="ai_engine.create_daily_snapshots",
)
def create_daily_snapshots():
    """
    Periodic task: create DailySnapshot records for all users.
    Run at midnight UTC via Celery Beat.
    """
    from datetime import date
    from django.db.models import Count, Avg
    from apps.users.models import User
    from apps.habits.models import Habit, HabitLog, BehaviorEvent
    from apps.memory.models import Message
    from apps.analytics.models import DailySnapshot

    today = date.today()
    active_users = User.objects.filter(is_active=True).only("id")
    created_count = 0

    for user in active_users:
        # Skip if snapshot already exists
        if DailySnapshot.objects.filter(user=user, snapshot_date=today).exists():
            continue

        # Habit stats
        active_habits = Habit.objects.filter(user=user, is_active=True).count()
        completed = HabitLog.objects.filter(user=user, log_date=today).count()

        # AI stats
        ai_msgs = Message.objects.filter(
            conversation__user=user,
            role="user",
            created_at__date=today,
        ).count()
        ai_sessions = Message.objects.filter(
            conversation__user=user,
            role="user",
            created_at__date=today,
        ).values("conversation_id").distinct().count()

        # Activity
        events_today = BehaviorEvent.objects.filter(user=user, occurred_at__date=today)
        active_hours = events_today.values("hour_of_day").distinct().count()
        peak_row = (
            events_today.values("hour_of_day")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")
            .first()
        )
        peak_hour = peak_row["hour_of_day"] if peak_row else None

        DailySnapshot.objects.create(
            user=user,
            snapshot_date=today,
            habits_completed=completed,
            habits_total=active_habits,
            habit_completion_rate=round(completed / active_habits * 100, 1) if active_habits else 0.0,
            ai_messages_sent=ai_msgs,
            ai_sessions=ai_sessions,
            active_hours=active_hours,
            peak_hour=peak_hour,
        )
        created_count += 1

    logger.info("Daily snapshots created", extra={"count": created_count})
    return {"status": "success", "created": created_count}
