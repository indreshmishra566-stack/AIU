from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GoalViewSet

router = DefaultRouter()
router.register(r"", GoalViewSet, basename="goals")
urlpatterns = [path("", include(router.urls))]
