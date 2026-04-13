from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

User = get_user_model()


def email_delivery_mode():
    if settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
        return "smtp"
    return "local"


def build_password_reset_url(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    query = urlencode({"reset_uid": uid, "reset_token": token})
    return f"{settings.SITE_URL}/app/?{query}"


def send_password_reset_email(user):
    reset_url = build_password_reset_url(user)
    subject = "Reset your Number Extractor password"
    message = (
        f"Hello {user.full_name},\n\n"
        f"Use the link below to reset your password:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
    return reset_url


def send_password_changed_email(user):
    subject = "Your Number Extractor password was changed"
    message = (
        f"Hello {user.full_name},\n\n"
        "Your password has been changed successfully.\n"
        "If this was not you, reset your password immediately and contact support."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


def resolve_password_reset_user(uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None

    if not default_token_generator.check_token(user, token):
        return None
    return user
