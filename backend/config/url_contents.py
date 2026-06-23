"""
AIU — URL Routers: all app URL configs
"""

# ── apps/users/urls/auth.py ───────────────────────────────────────────────────
AUTH_URLS = """
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views import RegisterView, LogoutView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
"""

# ── apps/users/urls/users.py ──────────────────────────────────────────────────
USERS_URLS = """
from django.urls import path
from apps.users.views import MeView, ChangePasswordView

urlpatterns = [
    path("me/", MeView.as_view(), name="user-me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
"""

# ── apps/memory/urls.py ───────────────────────────────────────────────────────
MEMORY_URLS = """
from django.urls import path
from apps.memory.views import InsightListView

urlpatterns = [
    path("insights/", InsightListView.as_view(), name="memory-insights"),
]
"""

# ── apps/habits/urls.py ───────────────────────────────────────────────────────
HABITS_URLS = """
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.habits.views import HabitViewSet

router = DefaultRouter()
router.register(r"", HabitViewSet, basename="habits")

urlpatterns = [path("", include(router.urls))]
"""

# ── apps/recommendations/urls.py ──────────────────────────────────────────────
RECS_URLS = """
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.recommendations.models import RecommendationViewSet

router = DefaultRouter()
router.register(r"", RecommendationViewSet, basename="recommendations")

urlpatterns = [path("", include(router.urls))]
"""

# ── apps/analytics/urls.py ────────────────────────────────────────────────────
ANALYTICS_URLS = """
from django.urls import path
from apps.analytics.views import DashboardStatsView, BehaviorTimelineView

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view(), name="analytics-dashboard"),
    path("behavior/", BehaviorTimelineView.as_view(), name="analytics-behavior"),
]
"""

# ── apps/ai_engine/urls.py ────────────────────────────────────────────────────
AI_URLS = """
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ai_engine.views import ChatView, ConversationViewSet

router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversations")

urlpatterns = [
    path("chat/", ChatView.as_view(), name="ai-chat"),
    path("", include(router.urls)),
]
"""

# ── Write all URL files ───────────────────────────────────────────────────────
import os

files = {
    "apps/users/urls/__init__.py": "",
    "apps/users/urls/auth.py": AUTH_URLS.strip(),
    "apps/users/urls/users.py": USERS_URLS.strip(),
    "apps/memory/urls.py": MEMORY_URLS.strip(),
    "apps/habits/urls.py": HABITS_URLS.strip(),
    "apps/recommendations/urls.py": RECS_URLS.strip(),
    "apps/analytics/urls.py": ANALYTICS_URLS.strip(),
    "apps/ai_engine/urls.py": AI_URLS.strip(),
}
