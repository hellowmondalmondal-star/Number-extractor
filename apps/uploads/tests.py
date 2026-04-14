from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.subscriptions.services import ensure_default_plans
from apps.uploads.serializers import UploadCreateSerializer
from apps.uploads.models import UploadedFile
from apps.uploads.services import PROCESSING_TIMEOUT_MESSAGE

User = get_user_model()


class UploadSerializerTests(TestCase):
    def test_rejects_unsupported_files(self):
        serializer = UploadCreateSerializer(
            data={"file": SimpleUploadedFile("notes.txt", b"12345", content_type="text/plain")}
        )
        self.assertFalse(serializer.is_valid())

    def test_accepts_csv_file(self):
        serializer = UploadCreateSerializer(
            data={"file": SimpleUploadedFile("contacts.csv", b"phone\n9876543210", content_type="text/csv")}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class UploadApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @override_settings(FREE_PLAN_DAILY_FILE_LIMIT=1)
    def test_upload_limit_returns_400_instead_of_server_error(self):
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
        user = User.objects.create_user(
            email="upload@example.com",
            full_name="Upload User",
            password="password123",
        )
        self.client.force_authenticate(user=user)
        ensure_default_plans()

        UploadedFile.objects.create(
            user=user,
            file=SimpleUploadedFile("existing.pdf", pdf_bytes, content_type="application/pdf"),
            original_name="existing.pdf",
            file_size=len(pdf_bytes),
            file_type=UploadedFile.FileTypeChoices.PDF,
        )

        response = self.client.post(
            reverse("upload"),
            {
                "file": SimpleUploadedFile("second.pdf", pdf_bytes, content_type="application/pdf"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Daily file upload limit reached", str(response.data))

    @override_settings(UPLOAD_PROCESSING_TIMEOUT_SECONDS=60)
    def test_upload_list_marks_stale_processing_upload_as_failed(self):
        pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
        user = User.objects.create_user(
            email="stale@example.com",
            full_name="Stale Upload",
            password="password123",
        )
        self.client.force_authenticate(user=user)

        uploaded_file = UploadedFile.objects.create(
            user=user,
            file=SimpleUploadedFile("stale.pdf", pdf_bytes, content_type="application/pdf"),
            original_name="stale.pdf",
            file_size=len(pdf_bytes),
            file_type=UploadedFile.FileTypeChoices.PDF,
            status=UploadedFile.StatusChoices.PROCESSING,
        )
        stale_time = timezone.now() - timedelta(seconds=61)
        UploadedFile.objects.filter(pk=uploaded_file.pk).update(
            upload_time=stale_time,
            processed_at=None,
            error_message="",
        )

        response = self.client.get(reverse("upload-list"))

        self.assertEqual(response.status_code, 200)
        uploaded_file.refresh_from_db()
        self.assertEqual(uploaded_file.status, UploadedFile.StatusChoices.FAILED)
        self.assertEqual(uploaded_file.error_message, PROCESSING_TIMEOUT_MESSAGE)
