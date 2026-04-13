from rest_framework import serializers

from apps.subscriptions.models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = (
            "id",
            "code",
            "name",
            "daily_file_limit",
            "daily_number_limit",
            "is_unlimited",
            "price",
        )
        read_only_fields = fields


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = (
            "id",
            "status",
            "started_at",
            "expires_at",
            "auto_renew",
            "plan",
        )
        read_only_fields = fields
