import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.subscriptions.models import UserSubscription
from apps.subscriptions.services import get_plan_by_code, upsert_user_subscription

User = get_user_model()


class Command(BaseCommand):
    help = "Create or update the primary admin user from CLI arguments or environment variables."

    def add_arguments(self, parser):
        parser.add_argument("--email", help="Admin email. Falls back to ADMIN_EMAIL.")
        parser.add_argument("--password", help="Admin password. Falls back to ADMIN_PASSWORD.")
        parser.add_argument("--full-name", help="Admin full name. Falls back to ADMIN_FULL_NAME.")
        parser.add_argument("--plan-code", help="Subscription plan code. Falls back to ADMIN_PLAN_CODE.")
        parser.add_argument(
            "--skip-if-missing",
            action="store_true",
            help="Exit successfully if the required admin environment variables are not set.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        email = (options.get("email") or os.getenv("ADMIN_EMAIL", "")).strip().lower()
        password = options.get("password") or os.getenv("ADMIN_PASSWORD", "")
        full_name = (options.get("full_name") or os.getenv("ADMIN_FULL_NAME", "Primary Admin")).strip()
        plan_code = (options.get("plan_code") or os.getenv("ADMIN_PLAN_CODE", "pro")).strip().lower() or "pro"

        if not email or not password:
            if options["skip_if_missing"]:
                self.stdout.write("Skipping admin bootstrap because ADMIN_EMAIL or ADMIN_PASSWORD is not set.")
                return
            raise CommandError("Provide --email/--password or set ADMIN_EMAIL and ADMIN_PASSWORD.")

        plan = get_plan_by_code(plan_code)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": full_name or "Primary Admin",
                "role": User.RoleChoices.ADMIN,
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        changed_fields = []
        desired_values = {
            "full_name": full_name or user.full_name or "Primary Admin",
            "role": User.RoleChoices.ADMIN,
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
        }

        for field, value in desired_values.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)

        # Keep the Render-provided password authoritative when this command runs.
        user.set_password(password)
        changed_fields.append("password")

        if created:
            user.save()
        else:
            user.save(update_fields=sorted(set(changed_fields)))

        upsert_user_subscription(
            user=user,
            plan=plan,
            status=UserSubscription.StatusChoices.ACTIVE,
            auto_renew=False,
        )

        action = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"{action} admin account for {user.email} with the {plan.code} plan.")
        )
