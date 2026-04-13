from django.contrib import admin

from apps.subscriptions.models import SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "daily_file_limit", "daily_number_limit", "is_unlimited", "price")
    list_filter = ("is_unlimited",)
    search_fields = ("name", "code")


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "started_at", "expires_at", "auto_renew")
    list_filter = ("status", "plan")
    search_fields = ("user__email", "plan__name")

# Register your models here.
