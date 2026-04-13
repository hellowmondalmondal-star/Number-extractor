import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


def upload_file_path(instance, filename):
    extension = Path(filename).suffix.lower()
    timestamp = timezone.now().strftime("%Y/%m/%d")
    return f"uploads/{instance.user_id}/{timestamp}/{uuid.uuid4().hex}{extension}"


class UploadedFile(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class FileTypeChoices(models.TextChoices):
        PDF = "pdf", "PDF"
        CSV = "csv", "CSV"
        EXCEL = "excel", "Excel"
        IMAGE = "image", "Image"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="uploads")
    file = models.FileField(upload_to=upload_file_path)
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FileTypeChoices.choices)
    file_size = models.PositiveBigIntegerField(default=0)
    upload_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-upload_time"]

    def __str__(self):
        return self.original_name

# Create your models here.
