from django.contrib import admin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "priority", "status", "confidence_score", "created_at")
    list_filter = ("category", "priority", "status")
    search_fields = ("title", "user__email", "description")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at")
