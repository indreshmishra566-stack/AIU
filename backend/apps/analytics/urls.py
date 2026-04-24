from django.urls import path
from apps.analytics.views import DashboardStatsView, BehaviorTimelineView
from apps.analytics.nudges import SmartNudgesView

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view(), name="analytics-dashboard"),
    path("behavior/",  BehaviorTimelineView.as_view(), name="analytics-behavior"),
    path("nudges/",    SmartNudgesView.as_view(), name="analytics-nudges"),
]
