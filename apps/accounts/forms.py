from django import forms
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.accounts.models import User
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.subscriptions.services import ensure_default_plans, get_plan_by_code, upsert_user_subscription


class SubscriptionFieldsMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ensure_default_plans()
        self.fields["plan"] = forms.ModelChoiceField(queryset=SubscriptionPlan.objects.order_by("name"), required=True)
        self.fields["subscription_status"] = forms.ChoiceField(
            choices=UserSubscription.StatusChoices.choices,
            initial=UserSubscription.StatusChoices.ACTIVE,
        )
        self.fields["subscription_expires_at"] = forms.SplitDateTimeField(
            required=False,
            widget=AdminSplitDateTime,
        )
        self.fields["subscription_auto_renew"] = forms.BooleanField(required=False, initial=True)

        self.fields["plan"].initial = get_plan_by_code("free")

        instance = getattr(self, "instance", None)
        if instance and instance.pk:
            try:
                subscription = instance.subscription
            except User.subscription.RelatedObjectDoesNotExist:
                subscription = None

            if subscription:
                self.fields["plan"].initial = subscription.plan
                self.fields["subscription_status"].initial = subscription.status
                self.fields["subscription_expires_at"].initial = subscription.expires_at
                self.fields["subscription_auto_renew"].initial = subscription.auto_renew

    def save_subscription(self, user):
        subscription = upsert_user_subscription(
            user=user,
            plan=self.cleaned_data["plan"],
            status=self.cleaned_data["subscription_status"],
            expires_at=self.cleaned_data.get("subscription_expires_at"),
            auto_renew=self.cleaned_data.get("subscription_auto_renew", False),
        )
        user.subscription = subscription


class AdminUserCreationForm(SubscriptionFieldsMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "full_name", "role", "is_active", "is_staff", "is_superuser")

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.role == User.RoleChoices.ADMIN:
            user.is_staff = True
        if commit:
            user.save()
            self.save_m2m()
            self.save_subscription(user)
        return user


class AdminUserChangeForm(SubscriptionFieldsMixin, UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.role == User.RoleChoices.ADMIN:
            user.is_staff = True
        if commit:
            user.save()
            self.save_m2m()
            self.save_subscription(user)
        return user
