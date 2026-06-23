from django.contrib import admin
from .models import DailySnapshot


@admin.register(DailySnapshot)
class DailySnapshotAdmin(admin.ModelAdmin):
    list_display = ("user", "snapshot_date", "habits_completed", "habits_total", "ai_messages_sent", "active_hours")
    list_filter = ("snapshot_date",)
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at")
    date_hierarchy = "snapshot_date"
