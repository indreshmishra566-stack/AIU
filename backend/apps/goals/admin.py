from django.contrib import admin
from .models import Goal, Milestone, GoalTask, GoalActivity

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "priority", "status", "progress_pct", "target_date", "created_at")
    list_filter  = ("status", "category", "priority", "extracted_from_chat")
    search_fields = ("title", "user__email", "description")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at", "completed_at")

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("title", "goal", "is_completed", "order", "target_date")
    list_filter  = ("is_completed",)
    raw_id_fields = ("goal",)

@admin.register(GoalTask)
class GoalTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "goal", "status", "due_date", "completed_at")
    list_filter  = ("status",)
    raw_id_fields = ("goal", "milestone")

@admin.register(GoalActivity)
class GoalActivityAdmin(admin.ModelAdmin):
    list_display = ("goal", "activity_type", "description", "occurred_at")
    list_filter  = ("activity_type",)
    raw_id_fields = ("goal", "user")
    readonly_fields = ("id", "occurred_at")
