from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.extraction.models import ExtractionResult
from apps.extraction.services import extract_numbers, extract_numbers_from_chunks, normalize_phone_number
from apps.uploads.models import UploadedFile

User = get_user_model()


class ExtractionServiceTests(TestCase):
    def test_normalize_phone_number_for_india_and_uae(self):
        self.assertEqual(normalize_phone_number("9876543210"), "+919876543210")
        self.assertEqual(normalize_phone_number("+971 50 123 4567"), "+971501234567")

    def test_extract_numbers_removes_duplicates(self):
        text = "Call +91 98765 43210 or 9876543210 or +971-50-123-4567."
        self.assertEqual(extract_numbers(text), ["+919876543210", "+971501234567"])

    def test_extract_numbers_keeps_separate_rows_as_separate_numbers(self):
        text = "phone\n9876543210\n9876543211\n"
        self.assertEqual(extract_numbers(text), ["+919876543210", "+919876543211"])

    def test_extract_numbers_from_chunks_deduplicates_across_streamed_content(self):
        chunks = ["+91 98765 43210", " and 9876543210", " plus +971 50 123 4567"]
        self.assertEqual(
            extract_numbers_from_chunks(chunks),
            ["+919876543210", "+971501234567"],
        )


class ExtractionApiTests(TestCase):
    def test_results_endpoint_returns_200_for_authenticated_user(self):
        user = User.objects.create_user(email="results@example.com", full_name="Results User", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse("result-list"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)

    @override_settings(FREE_PLAN_DAILY_NUMBER_LIMIT=1)
    def test_process_limit_returns_400_instead_of_server_error(self):
        user = User.objects.create_user(email="process@example.com", full_name="Process User", password="password123")
        client = APIClient()
        client.force_authenticate(user=user)

        csv_bytes = b"phone\n9876543210\n9876543211\n"
        uploaded_file = UploadedFile.objects.create(
            user=user,
            file=SimpleUploadedFile("contacts.csv", csv_bytes, content_type="text/csv"),
            original_name="contacts.csv",
            file_size=len(csv_bytes),
            file_type=UploadedFile.FileTypeChoices.CSV,
        )

        with patch(
            "apps.extraction.views.process_uploaded_file",
            side_effect=DjangoValidationError("Daily extracted number limit reached for the current subscription."),
        ):
            response = client.post(reverse("process-upload", args=[uploaded_file.id]))

        self.assertEqual(response.status_code, 400)
        self.assertIn("Daily extracted number limit reached", str(response.data))

    @override_settings(UPLOAD_PROCESSING_TIMEOUT_SECONDS=60)
    def test_process_endpoint_rejects_recent_processing_upload(self):
        user = User.objects.create_user(
            email="busy@example.com",
            full_name="Busy User",
            password="password123",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        csv_bytes = b"phone\n9876543210\n"
        uploaded_file = UploadedFile.objects.create(
            user=user,
            file=SimpleUploadedFile("busy.csv", csv_bytes, content_type="text/csv"),
            original_name="busy.csv",
            file_size=len(csv_bytes),
            file_type=UploadedFile.FileTypeChoices.CSV,
            status=UploadedFile.StatusChoices.PROCESSING,
        )

        response = client.post(reverse("process-upload", args=[uploaded_file.id]))

        self.assertEqual(response.status_code, 400)
        self.assertIn("already processing", str(response.data).lower())

    def test_process_endpoint_reuses_existing_completed_result(self):
        user = User.objects.create_user(
            email="done@example.com",
            full_name="Done User",
            password="password123",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        csv_bytes = b"phone\n9876543210\n"
        uploaded_file = UploadedFile.objects.create(
            user=user,
            file=SimpleUploadedFile("done.csv", csv_bytes, content_type="text/csv"),
            original_name="done.csv",
            file_size=len(csv_bytes),
            file_type=UploadedFile.FileTypeChoices.CSV,
            status=UploadedFile.StatusChoices.COMPLETED,
        )
        result = ExtractionResult.objects.create(
            user=user,
            upload=uploaded_file,
            numbers=["+919876543210"],
            total_numbers=1,
        )

        with patch("apps.extraction.views.process_uploaded_file") as mocked_process:
            response = client.post(reverse("process-upload", args=[uploaded_file.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.data["id"]), str(result.id))
        mocked_process.assert_not_called()
