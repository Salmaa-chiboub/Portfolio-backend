from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """Allows access only to superusers (is_superuser=True)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
