"""
AIU — Root URL Configuration
"""

from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from django.utils import timezone


def health_check(request):
    """Public health check endpoint. Used by Render/Railway/load balancers."""
    return JsonResponse({
        "status": "ok",
        "service": "aiu-backend",
        "timestamp": timezone.now().isoformat(),
    })
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_v1_patterns = [
    path("auth/", include("apps.users.urls.auth")),
    path("users/", include("apps.users.urls.users")),
    path("memory/", include("apps.memory.urls")),
    path("habits/", include("apps.habits.urls")),
    path("recommendations/", include("apps.recommendations.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("ai/", include("apps.ai_engine.urls")),
    path("goals/", include("apps.goals.urls")),
]

urlpatterns = [
    # Health check (public, no auth required)
    path("api/v1/health/", health_check, name="health-check"),

    # Admin
    path("admin/", admin.site.urls),

    # API v1
    path("api/v1/", include(api_v1_patterns)),

    # API Schema & Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Prometheus metrics
    path("", include("django_prometheus.urls")),
]
