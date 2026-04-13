from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.extraction.services import extract_numbers, normalize_phone_number

User = get_user_model()


class ExtractionServiceTests(TestCase):
    def test_normalize_phone_number_for_india_and_uae(self):
        self.assertEqual(normalize_phone_number("9876543210"), "+919876543210")
        self.assertEqual(normalize_phone_number("+971 50 123 4567"), "+971501234567")

    def test_extract_numbers_removes_duplicates(self):
        text = "Call +91 98765 43210 or 9876543210 or +971-50-123-4567."
        self.assertEqual(extract_numbers(text), ["+919876543210", "+971501234567"])


class ExtractionApiTests(TestCase):
    def test_results_endpoint_returns_200_for_authenticated_user(self):
        user = User.objects.create_user(email="results@example.com", full_name="Results User", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse("result-list"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
