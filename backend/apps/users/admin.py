from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import (
    UserChangeForm as BaseUserChangeForm,
    UserCreationForm as BaseUserCreationForm,
)
from .models import User, UserProfile, UserDevice


class UserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name", "role")


class UserChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = ("email", "first_name", "last_name", "role", "is_active", "date_joined", "last_activity")
    list_filter = ("role", "is_active", "is_email_verified", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_activity")
    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Personal", {"fields": ("first_name", "last_name", "phone_number")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser", "is_email_verified", "groups", "user_permissions")}),
        ("Timestamps", {"fields": ("date_joined", "last_activity")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2", "first_name", "last_name", "role")}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "coach_mode", "timezone", "onboarding_completed", "total_interactions")
    list_filter = ("coach_mode", "onboarding_completed")
    search_fields = ("user__email",)
    raw_id_fields = ("user",)


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ("user", "device_name", "ip_address", "is_trusted", "last_seen")
    list_filter = ("is_trusted",)
    search_fields = ("user__email", "ip_address")
    raw_id_fields = ("user",)
