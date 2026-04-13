from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.accounts.forms import AdminUserChangeForm, AdminUserCreationForm
from apps.accounts.models import User
from apps.subscriptions.models import UserSubscription

class UserSubscriptionInline(admin.StackedInline):
    model = UserSubscription
    can_delete = False
    verbose_name_plural = 'Subscription'
    fk_name = 'user'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm
    ordering = ("-date_joined",)
    list_display = ("email", "full_name", "role", "subscription_plan", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "full_name")
    inlines = (UserSubscriptionInline,)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
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
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
    def subscription_plan(self, obj):
        try:
            return obj.subscription.plan.name
        except User.subscription.RelatedObjectDoesNotExist:
            return "-"

    subscription_plan.short_description = "Subscription"

# Register your models here.