from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from apps.accounts.services import email_delivery_mode, send_password_changed_email, send_password_reset_email
from apps.accounts.permissions import IsAdminUserRole
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)
from apps.dashboard.services import log_activity

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    def get_permissions(self):
        if self.action in {"login", "forgot_password", "reset_password"}:
            return [permissions.AllowAny()]
        if self.action == "register" and not User.objects.exists():
            return [permissions.AllowAny()]
        if self.action == "register":
            return [IsAdminUserRole()]
        return [permissions.IsAuthenticated()]

    def register(self, request):
        payload = request.data.copy()

        if not User.objects.exists():
            payload["role"] = User.RoleChoices.ADMIN
        elif not request.user.is_admin:
            raise PermissionDenied("Only admins can create user accounts.")

        serializer = RegisterSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        actor = request.user if request.user.is_authenticated else user
        log_activity(
            user=actor,
            action="user_registered",
            description=f"Created account for {user.email}.",
            metadata={"created_user_id": user.id, "created_role": user.role},
        )

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def login(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        log_activity(user=user, action="login", description="User logged in.")

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )

    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError as exc:
            raise PermissionDenied("Refresh token is invalid or already revoked.") from exc

        log_activity(user=request.user, action="logout", description="User logged out.")
        return Response(status=status.HTTP_205_RESET_CONTENT)

    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])

        send_password_changed_email(request.user)
        log_activity(user=request.user, action="password_changed", description="User changed password.")
        return Response({"detail": "Password updated successfully."})

    def forgot_password(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        response_payload = {"detail": "If the account exists, a reset email has been sent."}
        user = User.objects.filter(email__iexact=serializer.validated_data["email"], is_active=True).first()
        if user:
            reset_url = send_password_reset_email(user)
            log_activity(user=user, action="password_reset_requested", description="Password reset email sent.")
            if email_delivery_mode() != "smtp":
                response_payload = {
                    "detail": "Email sending is not fully configured locally. Use the reset link below.",
                    "reset_url": reset_url,
                    "delivery_mode": "local",
                }

        return Response(response_payload)

    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        send_password_changed_email(user)
        log_activity(user=user, action="password_reset_completed", description="Password reset completed.")
        return Response({"detail": "Password reset successfully."})

    def me(self, request):
        queryset = User.objects.select_related("subscription__plan").annotate(upload_count=Count("uploads"))
        user = queryset.get(pk=request.user.pk)
        return Response(UserSerializer(user).data)
