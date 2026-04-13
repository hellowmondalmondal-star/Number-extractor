from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    message = "You can only access your own records."

    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and (request.user.is_admin or obj.user_id == request.user.id))
