"""
AIU — Users App: Serializers + Auth Views
Registration, login, token refresh, profile management.
"""

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import UserProfile

User = get_user_model()
logger = logging.getLogger("apps.users")


# ── Serializers ───────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=12, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    timezone = serializers.CharField(max_length=50, default="UTC")
    goals = serializers.ListField(
        child=serializers.CharField(max_length=200),
        max_length=10,
        required=False,
        default=list,
    )

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "coach_mode",
            "timezone",
            "language",
            "personality_traits",
            "behavior_patterns",
            "productivity_windows",
            "communication_style",
            "onboarding_completed",
            "goals",
            "total_interactions",
            "ai_satisfaction_score",
            "updated_at",
        ]
        read_only_fields = [
            "personality_traits",
            "behavior_patterns",
            "productivity_windows",
            "total_interactions",
            "ai_satisfaction_score",
            "updated_at",
        ]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_email_verified",
            "date_joined",
            "last_activity",
            "profile",
        ]
        read_only_fields = ["id", "role", "is_email_verified", "date_joined", "last_activity"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=12, write_only=True)

    def validate_new_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value


# ── Auth Views ────────────────────────────────────────────────────────────────

class LoginSerializer(TokenObtainPairSerializer):
    """Returns access/refresh tokens together with the user payload."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login/"""
    serializer_class = LoginSerializer


class RegisterView(APIView):
    """POST /api/v1/auth/register/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )
            UserProfile.objects.create(
                user=user,
                timezone=data.get("timezone", "UTC"),
                goals=data.get("goals", []),
            )

        # Issue tokens immediately
        refresh = RefreshToken.for_user(user)
        logger.info("User registered", extra={"user_id": str(user.id)})

        return Response(
            {
                "status": "success",
                "message": "Account created.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"status": "error", "message": "refresh token required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass  # Already blacklisted or invalid — that's fine
        return Response({"status": "success", "message": "Logged out."})


class MeView(APIView):
    """GET /api/v1/users/me/ — current user + profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user.update_last_activity()
        return Response(
            {"status": "success", "data": UserSerializer(user).data}
        )

    def patch(self, request):
        """Update display name + profile preferences."""
        user = request.user

        # User-level fields
        user_fields = {k: v for k, v in request.data.items() if k in ("first_name", "last_name")}
        if user_fields:
            for field, value in user_fields.items():
                setattr(user, field, value)
            user.save(update_fields=list(user_fields.keys()))

        # Profile-level fields
        profile_data = {
            k: v for k, v in request.data.items()
            if k in ("coach_mode", "timezone", "language", "communication_style", "goals", "onboarding_completed")
        }
        if profile_data:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile_serializer = UserProfileSerializer(profile, data=profile_data, partial=True)
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()

        return Response({"status": "success", "data": UserSerializer(user).data})


class ChangePasswordView(APIView):
    """POST /api/v1/users/change-password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"status": "error", "message": "Current password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        # Blacklist all existing refresh tokens so old sessions cannot be reused.
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )
        for outstanding in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=outstanding)

        logger.info("Password changed", extra={"user_id": str(user.id)})
        return Response({"status": "success", "message": "Password updated."})
