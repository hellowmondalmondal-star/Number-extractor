from django.urls import path

from apps.subscriptions.views import SubscriptionViewSet

urlpatterns = [
    path("subscription/me", SubscriptionViewSet.as_view({"get": "me"}), name="subscription-me"),
]
