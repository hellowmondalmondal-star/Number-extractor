from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.subscriptions.services import enforce_daily_file_limit, enforce_daily_number_limit, ensure_default_plans

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

    @override_settings(
        FREE_PLAN_DAILY_FILE_LIMIT=1,
        FREE_PLAN_DAILY_NUMBER_LIMIT=1,
    )
    def test_admin_users_are_not_limited_by_subscription_rules(self):
        admin = User.objects.create_user(
            email="admin@example.com",
            full_name="Admin User",
            password="password123",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
            is_superuser=True,
        )

        self.assertIsNone(enforce_daily_file_limit(admin))
        self.assertIsNone(enforce_daily_number_limit(admin, incoming_total=999))
