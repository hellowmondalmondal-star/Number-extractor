from django.contrib.auth import authenticate, get_user_model, password_validation
from rest_framework import serializers

from apps.accounts.services import resolve_password_reset_user
from apps.subscriptions.services import assign_user_plan, ensure_default_plans

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    subscription_plan = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "full_name",
            "role",
            "is_active",
            "date_joined",
            "subscription_plan",
        )
        read_only_fields = fields

    def get_subscription_plan(self, obj):
        try:
            subscription = obj.subscription
        except User.subscription.RelatedObjectDoesNotExist:
            subscription = None
        if not subscription:
            return None
        return subscription.plan.code


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    plan_code = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = User
        fields = ("email", "full_name", "role", "password", "password_confirm", "plan_code")
        extra_kwargs = {"role": {"required": False}}

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        password_validation.validate_password(attrs["password"])
        return attrs

    def validate_plan_code(self, value):
        if not value:
            return value
        plans = ensure_default_plans()
        if value.lower() not in plans:
            raise serializers.ValidationError("Invalid subscription plan.")
        return value.lower()

    def create(self, validated_data):
        plan_code = validated_data.pop("plan_code", "").strip().lower() or "free"
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        role = validated_data.get("role", User.RoleChoices.AGENT)
        if role == User.RoleChoices.ADMIN:
            validated_data["is_staff"] = True
            validated_data["is_superuser"] = True
        else:
            validated_data["is_staff"] = False
            validated_data["is_superuser"] = False
        user = User.objects.create_user(password=password, **validated_data)
        assign_user_plan(user, plan_code)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(request=request, username=attrs["email"], password=attrs["password"])
        if not user or not user.is_active:
            raise serializers.ValidationError("Invalid credentials.")
        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        password_validation.validate_password(attrs["new_password"], user=user)
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        user = resolve_password_reset_user(attrs["uid"], attrs["token"])
        if not user:
            raise serializers.ValidationError("Reset link is invalid or expired.")
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        password_validation.validate_password(attrs["new_password"], user=user)
        attrs["user"] = user
        return attrs
