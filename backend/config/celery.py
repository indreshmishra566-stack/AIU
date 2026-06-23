"""
AIU — Celery Application Configuration
"""

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("aiu")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.autodiscover_tasks(["apps.ai_engine"], related_name="tasks_goals")

# ── Periodic Tasks (Celery Beat) ──────────────────────────────────────────────
app.conf.beat_schedule = {
    # Daily recommendations at 7am UTC
    "daily-recommendations": {
        "task": "ai_engine.generate_daily_recommendations",
        "schedule": crontab(hour=7, minute=0),
    },
    # Purge old behavior events (keep 90 days)
    # Daily snapshots at midnight UTC
    "create-daily-snapshots": {
        "task": "ai_engine.create_daily_snapshots",
        "schedule": crontab(hour=0, minute=5),
    },
    "purge-old-events": {
        "task": "ai_engine.purge_old_behavior_events",
        "schedule": crontab(hour=2, minute=0),
    },
    # Re-analyze behavior patterns for active users (weekly)
    "weekly-behavior-analysis": {
        "task": "ai_engine.run_weekly_behavior_analysis",
        "schedule": crontab(day_of_week=1, hour=3, minute=0),
    },
}

app.conf.task_routes = {
    "ai_engine.store_message_embedding": {"queue": "embeddings"},
    "ai_engine.extract_insights_*": {"queue": "ai_processing"},
    "ai_engine.summarize_*": {"queue": "ai_processing"},
    "ai_engine.analyze_*": {"queue": "ai_processing"},
    "ai_engine.generate_*": {"queue": "ai_processing"},
    "ai_engine.update_behavior_patterns": {"queue": "analytics"},
    "ai_engine.extract_goals_*": {"queue": "ai_processing"},
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
