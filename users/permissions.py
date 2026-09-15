from rest_framework.permissions import BasePermission

from .models import UserRole


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


class IsBusinessDeveloper(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and UserRole.objects.filter(
                user=request.user,
                role__name="BD",
            ).exists()
        )


class IsTechnicalManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and UserRole.objects.filter(
                user=request.user,
                role__name="Technical Manager",
            ).exists()
        )


class IsEngineer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and UserRole.objects.filter(
                user=request.user,
                role__name="Engineer",
            ).exists()
        )
