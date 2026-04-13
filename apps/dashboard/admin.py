from django.contrib import admin

from apps.dashboard.models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "description", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("action", "description", "user__email")

# Register your models here.
