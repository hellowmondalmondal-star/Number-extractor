from django.core import mail
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient
from django.contrib.auth.tokens import default_token_generator

from apps.accounts.forms import AdminUserCreationForm
from apps.accounts.serializers import RegisterSerializer
from apps.subscriptions.services import get_plan_by_code

User = get_user_model()


class RegisterSerializerTests(TestCase):
    def test_creates_user_with_default_free_plan(self):
        serializer = RegisterSerializer(
            data={
                "email": "agent@example.com",
                "full_name": "Agent One",
                "role": "agent",
                "password": "OrbitPass5481",
                "password_confirm": "OrbitPass5481",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertEqual(user.email, "agent@example.com")
        self.assertEqual(user.subscription.plan.code, "free")


class AdminUserCreationFormTests(TestCase):
    def test_admin_user_creation_form_sets_subscription(self):
        pro_plan = get_plan_by_code("pro")
        form = AdminUserCreationForm(
            data={
                "email": "agent-pro@example.com",
                "full_name": "Agent Pro",
                "role": "agent",
                "plan": str(pro_plan.pk),
                "subscription_status": "active",
                "subscription_auto_renew": "on",
                "is_active": "on",
                "password1": "OrbitPass5481",
                "password2": "OrbitPass5481",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertEqual(user.subscription.plan.code, "pro")
        self.assertEqual(user.subscription.status, "active")


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SITE_URL="http://testserver",
)
class PasswordFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="flow@example.com",
            full_name="Flow User",
            password="OrbitPass5481",
        )
        self.client = APIClient()

    def test_forgot_password_sends_email(self):
        response = self.client.post(reverse("forgot-password"), {"email": self.user.email}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset_uid=", mail.outbox[0].body)
        self.assertIn("reset_token=", mail.outbox[0].body)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_forgot_password_returns_reset_link_for_local_delivery(self):
        response = self.client.post(reverse("forgot-password"), {"email": self.user.email}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["delivery_mode"], "local")
        self.assertIn("reset_uid=", response.data["reset_url"])
        self.assertIn("reset_token=", response.data["reset_url"])

    def test_reset_password_updates_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            reverse("reset-password"),
            {
                "uid": uid,
                "token": token,
                "new_password": "NorthStar5481",
                "new_password_confirm": "NorthStar5481",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NorthStar5481"))

    def test_change_password_updates_password_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("change-password"),
            {
                "current_password": "OrbitPass5481",
                "new_password": "CometTrail5481",
                "new_password_confirm": "CometTrail5481",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("CometTrail5481"))
