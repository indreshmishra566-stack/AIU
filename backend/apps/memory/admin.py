from django.contrib import admin
from .models import Conversation, Message, MemoryEmbedding, MemoryInsight


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "coach_mode", "is_archived", "started_at", "last_message_at")
    list_filter = ("is_archived", "coach_mode")
    search_fields = ("user__email", "title", "summary")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "started_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "model_used", "prompt_tokens", "completion_tokens", "created_at")
    list_filter = ("role", "model_used")
    search_fields = ("content",)
    raw_id_fields = ("conversation",)
    readonly_fields = ("id", "created_at")


@admin.register(MemoryEmbedding)
class MemoryEmbeddingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "source_type", "importance_score", "access_count", "created_at")
    list_filter = ("source_type",)
    search_fields = ("user__email", "content")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "content_hash", "created_at")
    exclude = ("embedding",)  # Don't display raw vectors in admin


@admin.register(MemoryInsight)
class MemoryInsightAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "insight_type", "confidence", "evidence_count", "is_active", "created_at")
    list_filter = ("insight_type", "is_active")
    search_fields = ("user__email", "content")
    raw_id_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")
