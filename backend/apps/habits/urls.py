from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.habits.views import HabitViewSet

router = DefaultRouter()
router.register(r"", HabitViewSet, basename="habits")
urlpatterns = [path("", include(router.urls))]
