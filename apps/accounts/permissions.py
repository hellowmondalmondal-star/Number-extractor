from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):
    message = "Admin access is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsAgentUserRole(BasePermission):
    message = "Agent access is required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "agent")
