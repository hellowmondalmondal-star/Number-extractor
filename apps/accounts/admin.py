from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.forms import AdminUserChangeForm, AdminUserCreationForm
from apps.accounts.models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    ordering = ("-date_joined",)
    list_display = ("email", "full_name", "role", "subscription_plan", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("email", "full_name")
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role")}),
        (
            "Subscription",
            {
                "fields": (
                    "plan",
                    "subscription_status",
                    "subscription_expires_at",
                    "subscription_auto_renew",
                )
            },
        ),
        ("Permissions", {"fields": ("is_active", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "role",
                    "plan",
                    "subscription_status",
                    "subscription_expires_at",
                    "subscription_auto_renew",
                    "password1",
                    "password2",
                    "is_active",
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if hasattr(form, "save_subscription"):
            form.save_subscription(obj)

    def subscription_plan(self, obj):
        try:
            return obj.subscription.plan.name
        except User.subscription.RelatedObjectDoesNotExist:
            return "-"

    subscription_plan.short_description = "Subscription"
