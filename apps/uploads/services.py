from pathlib import Path

from django.conf import settings
from rest_framework.exceptions import ValidationError

ALLOWED_FILE_TYPES = {
    ".pdf": "pdf",
    ".csv": "csv",
    ".xls": "excel",
    ".xlsx": "excel",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".webp": "image",
}


def detect_file_type(filename):
    extension = Path(filename).suffix.lower()
    file_type = ALLOWED_FILE_TYPES.get(extension)
    if not file_type:
        raise ValidationError("Unsupported file type. Allowed formats: PDF, CSV, Excel, images.")
    return file_type


def validate_file_object(file_obj):
    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_obj.size > max_size_bytes:
        raise ValidationError(f"File size exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit.")
    detect_file_type(file_obj.name)
    return file_obj
