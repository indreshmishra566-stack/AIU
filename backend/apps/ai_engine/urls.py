from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ai_engine.views import ChatView, ConversationViewSet

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversations")

urlpatterns = [
    path("chat/", ChatView.as_view(), name="ai-chat"),
    path("", include(router.urls)),
]
