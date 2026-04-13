from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.uploads.serializers import UploadCreateSerializer


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

# Create your tests here.
