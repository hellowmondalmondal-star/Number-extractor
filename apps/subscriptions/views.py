from rest_framework import permissions, response, viewsets

from apps.subscriptions.serializers import UserSubscriptionSerializer
from apps.subscriptions.services import get_or_create_user_subscription


class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def me(self, request):
        subscription = get_or_create_user_subscription(request.user)
        return response.Response(UserSubscriptionSerializer(subscription).data)
