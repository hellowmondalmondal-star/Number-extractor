from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.dashboard.services import log_activity

User = get_user_model()


class DashboardServiceTests(TestCase):
    def test_log_activity_creates_entry(self):
        user = User.objects.create_user(email="audit@example.com", full_name="Audit User", password="password123")
        entry = log_activity(user=user, action="unit_test", description="Created in test.")
        self.assertEqual(entry.user, user)
        self.assertEqual(entry.action, "unit_test")

    def test_home_page_renders(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_app_page_renders(self):
        response = self.client.get(reverse("app"))
        self.assertEqual(response.status_code, 200)

# Create your tests here.
