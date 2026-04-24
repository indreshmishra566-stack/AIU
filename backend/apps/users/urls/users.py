from django.urls import path
from apps.users.views import MeView, ChangePasswordView

urlpatterns = [
    path("me/", MeView.as_view(), name="user-me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
