from django.contrib import admin

from apps.extraction.models import ExtractionResult


@admin.register(ExtractionResult)
class ExtractionResultAdmin(admin.ModelAdmin):
    list_display = ("upload", "user", "total_numbers", "created_at")
    list_filter = ("created_at",)
    search_fields = ("upload__original_name", "user__email")

# Register your models here.
