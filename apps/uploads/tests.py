from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.subscriptions.services import ensure_default_plans
from apps.uploads.serializers import UploadCreateSerializer
from apps.uploads.models import UploadedFile

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
