from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.subscriptions.services import enforce_daily_file_limit, ensure_default_plans

User = get_user_model()


class SubscriptionServiceTests(TestCase):
    def test_default_plans_exist(self):
        plans = ensure_default_plans()
        self.assertIn("free", plans)
        self.assertIn("pro", plans)

    def test_new_user_has_subscription(self):
        user = User.objects.create_user(email="plan@example.com", full_name="Plan User", password="password123")
        self.assertEqual(user.subscription.plan.code, "free")

    def test_file_limit_check_returns_subscription_for_free_plan(self):
        user = User.objects.create_user(email="agent2@example.com", full_name="Agent Two", password="password123")
        subscription = enforce_daily_file_limit(user)
        self.assertEqual(subscription.plan.code, "free")

# Create your tests here.
