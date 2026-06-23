"""
AIU — Users App: Custom Permissions
Role-based access control helpers for DRF views.
"""

from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """Allow access only to the object's owner (obj.user == request.user)."""

    def has_object_permission(self, request, view, obj):
        user = getattr(obj, "user", None) or getattr(obj, "user_id", None)
        if user is None:
            return False
        if hasattr(user, "pk"):
            return user.pk == request.user.pk
        return str(user) == str(request.user.pk)


class IsPremiumUser(BasePermission):
    """Allow access only to premium/admin/staff users."""

    message = "This feature requires a premium subscription."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_premium
        )


class IsAdminUser(BasePermission):
    """Allow access only to admin/staff users."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("admin", "staff")
        )


class IsOwnerOrAdmin(BasePermission):
    """Allow access to the object owner OR admin/staff users."""

    def has_object_permission(self, request, view, obj):
        if request.user.role in ("admin", "staff"):
            return True
        user = getattr(obj, "user", None) or getattr(obj, "user_id", None)
        if user is None:
            return False
        if hasattr(user, "pk"):
            return user.pk == request.user.pk
        return str(user) == str(request.user.pk)


class ReadOnly(BasePermission):
    """Allow GET/HEAD/OPTIONS only."""

    def has_permission(self, request, view):
        return request.method in ("GET", "HEAD", "OPTIONS")
