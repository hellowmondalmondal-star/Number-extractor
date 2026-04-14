from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.uploads.models import UploadedFile

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
PROCESSING_TIMEOUT_MESSAGE = "Processing timed out on the server. Please try again."


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


def processing_timeout_cutoff(now=None):
    return (now or timezone.now()) - timedelta(seconds=settings.UPLOAD_PROCESSING_TIMEOUT_SECONDS)


def mark_stale_processing_upload(uploaded_file, now=None):
    if uploaded_file.status != UploadedFile.StatusChoices.PROCESSING:
        return False

    now = now or timezone.now()
    reference_time = uploaded_file.processed_at or uploaded_file.upload_time
    if not reference_time or reference_time > processing_timeout_cutoff(now):
        return False

    uploaded_file.status = UploadedFile.StatusChoices.FAILED
    uploaded_file.error_message = PROCESSING_TIMEOUT_MESSAGE
    uploaded_file.processed_at = now
    uploaded_file.save(update_fields=["status", "error_message", "processed_at"])
    return True


def mark_stale_processing_uploads(queryset):
    now = timezone.now()
    cutoff = processing_timeout_cutoff(now)
    return queryset.filter(status=UploadedFile.StatusChoices.PROCESSING).filter(
        Q(processed_at__lte=cutoff) | Q(processed_at__isnull=True, upload_time__lte=cutoff)
    ).update(
        status=UploadedFile.StatusChoices.FAILED,
        error_message=PROCESSING_TIMEOUT_MESSAGE,
        processed_at=now,
    )
