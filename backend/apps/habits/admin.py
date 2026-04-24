from django.contrib import admin
from .models import Habit, HabitLog, BehaviorEvent


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "category", "frequency", "current_streak", "longest_streak", "is_active")
    list_filter = ("category", "frequency", "is_active")
    search_fields = ("name", "user__email")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ("habit", "user", "log_date", "completed_count", "mood_rating")
    list_filter = ("log_date",)
    search_fields = ("habit__name", "user__email")
    raw_id_fields = ("habit", "user")
    date_hierarchy = "log_date"


@admin.register(BehaviorEvent)
class BehaviorEventAdmin(admin.ModelAdmin):
    list_display = ("user", "event_type", "hour_of_day", "day_of_week", "occurred_at")
    list_filter = ("event_type", "hour_of_day", "day_of_week")
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
    readonly_fields = ("id", "occurred_at")
    date_hierarchy = "occurred_at"
