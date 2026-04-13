from django.contrib import admin

from apps.uploads.models import UploadedFile


@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ("original_name", "user", "file_type", "status", "upload_time", "processed_at")
    list_filter = ("file_type", "status", "upload_time")
    search_fields = ("original_name", "user__email")

# Register your models here.
