from django.urls import path
from apps.memory.views import InsightListView

urlpatterns = [
    path("insights/", InsightListView.as_view(), name="memory-insights"),
]
