import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone


def result_file_path(instance, filename):
    extension = Path(filename).suffix.lower() or ".xlsx"
    timestamp = timezone.now().strftime("%Y/%m/%d")
    return f"results/{instance.user_id}/{timestamp}/{uuid.uuid4().hex}{extension}"


class ExtractionResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="results")
    upload = models.OneToOneField("uploads.UploadedFile", on_delete=models.CASCADE, related_name="extraction_result")
    numbers = models.JSONField(default=list)
    total_numbers = models.PositiveIntegerField(default=0)
    result_file = models.FileField(upload_to=result_file_path, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.upload.original_name} ({self.total_numbers})"

# Create your models here.
