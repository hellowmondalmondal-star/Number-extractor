from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.dashboard.models import ActivityLog
from apps.extraction.serializers import ExtractionResultSerializer
from apps.subscriptions.serializers import UserSubscriptionSerializer
from apps.uploads.serializers import UploadSerializer

User = get_user_model()


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ActivityLog
        fields = ("id", "action", "description", "metadata", "created_at", "user_email")
        read_only_fields = fields


class AdminUserSerializer(serializers.ModelSerializer):
    subscription_plan = serializers.SerializerMethodField()
    upload_count = serializers.IntegerField(read_only=True)
    result_count = serializers.IntegerField(read_only=True)

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
            "upload_count",
            "result_count",
        )
        read_only_fields = fields

    def get_subscription_plan(self, obj):
        try:
            subscription = obj.subscription
        except User.subscription.RelatedObjectDoesNotExist:
            subscription = None
        return subscription.plan.code if subscription else None


class AgentDashboardSerializer(serializers.Serializer):
    stats = serializers.DictField()
    subscription = UserSubscriptionSerializer()
    recent_uploads = UploadSerializer(many=True)
    recent_results = ExtractionResultSerializer(many=True)
