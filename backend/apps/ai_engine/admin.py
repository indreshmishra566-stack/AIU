"""
AIU — AI Engine: Django Admin
The AI engine has no models of its own. All AI-related data
(conversations, messages, embeddings, insights) is registered
in the memory app admin. Celery task results are visible via
django-celery-results in the admin.
"""

from django.contrib import admin
from django_celery_results.models import TaskResult
from django_celery_beat.models import PeriodicTask, CrontabSchedule


# Unregister default celery-results registration so we can customise it
try:
    admin.site.unregister(TaskResult)
except admin.sites.NotRegistered:
    pass


@admin.register(TaskResult)
class TaskResultAdmin(admin.ModelAdmin):
    list_display = ("task_id", "task_name", "status", "date_created", "date_done")
    list_filter  = ("status", "task_name")
    search_fields = ("task_id", "task_name")
    readonly_fields = ("task_id", "task_name", "status", "result", "traceback",
                       "meta", "date_created", "date_done")
    ordering = ("-date_created",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
