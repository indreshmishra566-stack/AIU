"""
AIU — Users App: Models
Custom User model + RBAC roles + UserProfile
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from encrypted_model_fields.fields import EncryptedCharField

from .managers import UserManager


class Role(models.TextChoices):
    USER = "user", _("User")
    PREMIUM = "premium", _("Premium")
    ADMIN = "admin", _("Admin")
    STAFF = "staff", _("Staff")


class CoachMode(models.TextChoices):
    MENTOR = "mentor", _("Mentor")
    STRICT = "strict", _("Strict Coach")
    FRIENDLY = "friendly", _("Friendly Guide")
    ANALYTICAL = "analytical", _("Analytical Advisor")


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model. Uses email as username.
    Sensitive fields are encrypted at rest.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        db_index=True,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(null=True, blank=True)

    # Encrypted sensitive field example
    phone_number = EncryptedCharField(max_length=20, blank=True, default="")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        verbose_name = _("user")
        verbose_name_plural = _("users")
        indexes = [
            models.Index(fields=["email", "is_active"]),
            models.Index(fields=["role", "is_active"]),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_premium(self) -> bool:
        return self.role in (Role.PREMIUM, Role.ADMIN, Role.STAFF)

    def update_last_activity(self):
        User.objects.filter(pk=self.pk).update(last_activity=timezone.now())


class UserProfile(models.Model):
    """
    Extended profile. Updated dynamically by the behavior engine.
    Stores personality/preference data used by the AI layer.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    # AI coaching preferences
    coach_mode = models.CharField(
        max_length=20,
        choices=CoachMode.choices,
        default=CoachMode.FRIENDLY,
    )
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")

    # Dynamic personality/behavior data (updated by AI workers)
    personality_traits = models.JSONField(default=dict, blank=True)
    behavior_patterns = models.JSONField(default=dict, blank=True)
    productivity_windows = models.JSONField(default=list, blank=True)  # peak hours
    communication_style = models.CharField(max_length=50, default="balanced")

    # Onboarding
    onboarding_completed = models.BooleanField(default=False)
    goals = models.JSONField(default=list, blank=True)

    # Metrics (aggregate, updated by workers)
    total_interactions = models.PositiveIntegerField(default=0)
    ai_satisfaction_score = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"Profile:{self.user.email}"


class UserDevice(models.Model):
    """Track user devices for security auditing."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="devices")
    device_fingerprint = models.CharField(max_length=64, db_index=True)
    device_name = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_trusted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_devices"
        unique_together = [["user", "device_fingerprint"]]
