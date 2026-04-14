from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone

from apps.subscriptions.models import SubscriptionPlan, UserSubscription


def get_default_plan_definitions():
    return {
        "free": {
            "name": "Free",
            "daily_file_limit": settings.FREE_PLAN_DAILY_FILE_LIMIT,
            "daily_number_limit": settings.FREE_PLAN_DAILY_NUMBER_LIMIT,
            "is_unlimited": False,
            "price": 0,
        },
        "pro": {
            "name": "Pro",
            "daily_file_limit": None if settings.PRO_PLAN_DAILY_FILE_LIMIT == 0 else settings.PRO_PLAN_DAILY_FILE_LIMIT,
            "daily_number_limit": None
            if settings.PRO_PLAN_DAILY_NUMBER_LIMIT == 0
            else settings.PRO_PLAN_DAILY_NUMBER_LIMIT,
            "is_unlimited": settings.PRO_PLAN_DAILY_FILE_LIMIT == 0 and settings.PRO_PLAN_DAILY_NUMBER_LIMIT == 0,
            "price": 49,
        },
    }


def ensure_default_plans():
    plans = {}
    for code, defaults in get_default_plan_definitions().items():
        plan, _ = SubscriptionPlan.objects.update_or_create(code=code, defaults=defaults)
        plans[code] = plan
    return plans


def get_plan_by_code(code):
    plans = ensure_default_plans()
    try:
        return plans[code]
    except KeyError as exc:
        raise ValidationError("Invalid subscription plan.") from exc


def assign_user_plan(user, plan_code="free"):
    return upsert_user_subscription(user=user, plan_code=plan_code, status=UserSubscription.StatusChoices.ACTIVE)


def upsert_user_subscription(
    user,
    plan=None,
    plan_code="free",
    status=UserSubscription.StatusChoices.ACTIVE,
    expires_at=None,
    auto_renew=True,
):
    plan = plan or get_plan_by_code(plan_code)
    subscription, _ = UserSubscription.objects.update_or_create(
        user=user,
        defaults={
            "plan": plan,
            "status": status,
            "expires_at": expires_at,
            "auto_renew": auto_renew,
        },
    )
    return subscription


def get_or_create_user_subscription(user):
    plan = get_plan_by_code("free")
    subscription, _ = UserSubscription.objects.get_or_create(
        user=user,
        defaults={"plan": plan, "status": UserSubscription.StatusChoices.ACTIVE},
    )
    return subscription


def enforce_daily_file_limit(user):
    if getattr(user, "is_admin", False):
        return None

    subscription = get_or_create_user_subscription(user)
    plan = subscription.plan

    if plan.is_unlimited or plan.daily_file_limit in (None, 0):
        return subscription

    from apps.uploads.models import UploadedFile

    uploads_today = UploadedFile.objects.filter(user=user, upload_time__date=timezone.localdate()).count()
    if uploads_today >= plan.daily_file_limit:
        raise ValidationError("Daily file upload limit reached for the current subscription.")
    return subscription


def enforce_daily_number_limit(user, incoming_total, existing_total=0):
    if getattr(user, "is_admin", False):
        return None

    subscription = get_or_create_user_subscription(user)
    plan = subscription.plan

    if plan.is_unlimited or plan.daily_number_limit in (None, 0):
        return subscription

    from apps.extraction.models import ExtractionResult

    total_extracted = (
        ExtractionResult.objects.filter(user=user, created_at__date=timezone.localdate()).aggregate(
            total=Sum("total_numbers")
        )["total"]
        or 0
    )

    adjusted_total = max(total_extracted - existing_total, 0) + incoming_total
    if adjusted_total > plan.daily_number_limit:
        raise ValidationError("Daily extracted number limit reached for the current subscription.")
    return subscription
