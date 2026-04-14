import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


LOCAL_HOSTNAMES = {"127.0.0.1", "localhost", "::1"}


def unique_values(values):
    return list(dict.fromkeys(value for value in values if value))


def normalize_host(value):
    candidate = value.strip().rstrip("/")
    if not candidate:
        return ""

    parsed = urlparse(candidate if "://" in candidate else f"//{candidate}")
    return (parsed.hostname or candidate).strip()


def normalize_origin(value):
    candidate = value.strip().rstrip("/")
    if not candidate:
        return ""

    parsed = urlparse(candidate if "://" in candidate else f"//{candidate}")
    host = parsed.hostname
    if not host or host == "*":
        return ""

    if host.startswith("."):
        host = f"*{host}"

    base_host = host[2:] if host.startswith("*.") else host.lstrip(".")
    scheme = parsed.scheme or ("http" if base_host in LOCAL_HOSTNAMES else "https")
    if ":" in host and not host.startswith("[") and not host.startswith("*."):
        host = f"[{host}]"

    port = f":{parsed.port}" if parsed.port else ""
    return f"{scheme}://{host}{port}"


def normalize_hosts(values):
    return unique_values(normalize_host(value) for value in values)


def normalize_origins(values):
    return unique_values(normalize_origin(value) for value in values)


def build_allowed_hosts(*, configured_hosts, site_url, debug, render_external_hostname=""):
    resolved_hosts = []

    if debug:
        resolved_hosts.extend(["127.0.0.1", "localhost"])

    site_host = normalize_host(site_url)
    if site_host and (debug or site_url != DEFAULT_SITE_URL):
        resolved_hosts.append(site_host)

    render_host = normalize_host(render_external_hostname)
    if render_host:
        resolved_hosts.append(render_host)

    return unique_values(normalize_hosts(configured_hosts) + resolved_hosts)


def build_csrf_trusted_origins(*, configured_origins, site_url, debug, render_external_hostname=""):
    resolved_origins = []

    site_origin = normalize_origin(site_url)
    if site_origin and (debug or site_origin != DEFAULT_SITE_URL):
        resolved_origins.append(site_origin)

    render_origin = normalize_origin(render_external_hostname)
    if render_origin:
        resolved_origins.append(render_origin)

    return unique_values(normalize_origins(configured_origins) + resolved_origins)


DJANGO_ENV = os.getenv("DJANGO_ENV", "development").strip().lower()
DEFAULT_SECRET_KEY = "django-insecure-change-me"
DEFAULT_SITE_URL = "http://127.0.0.1:8000"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", DEFAULT_SECRET_KEY)
DEBUG = env_bool("DJANGO_DEBUG", default=DJANGO_ENV != "production")
SITE_URL = normalize_origin(os.getenv("SITE_URL", DEFAULT_SITE_URL)) or DEFAULT_SITE_URL
RENDER_EXTERNAL_HOSTNAME = normalize_host(os.getenv("RENDER_EXTERNAL_HOSTNAME", ""))

configured_allowed_hosts = normalize_hosts(env_list("DJANGO_ALLOWED_HOSTS"))
ALLOWED_HOSTS = build_allowed_hosts(
    configured_hosts=configured_allowed_hosts,
    site_url=SITE_URL,
    debug=DEBUG,
    render_external_hostname=RENDER_EXTERNAL_HOSTNAME,
)

configured_csrf_trusted_origins = normalize_origins(env_list("DJANGO_CSRF_TRUSTED_ORIGINS"))
CSRF_TRUSTED_ORIGINS = build_csrf_trusted_origins(
    configured_origins=configured_csrf_trusted_origins,
    site_url=SITE_URL,
    debug=DEBUG,
    render_external_hostname=RENDER_EXTERNAL_HOSTNAME,
)

if DJANGO_ENV == "production" and SECRET_KEY == DEFAULT_SECRET_KEY:
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY before running in production.")

if (
    DJANGO_ENV == "production"
    and not configured_allowed_hosts
    and not RENDER_EXTERNAL_HOSTNAME
    and SITE_URL == DEFAULT_SITE_URL
):
    raise ImproperlyConfigured("Set DJANGO_ALLOWED_HOSTS or SITE_URL before running in production.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "apps.accounts",
    "apps.subscriptions",
    "apps.uploads",
    "apps.extraction",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "UTC")

USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": int(os.getenv("API_PAGE_SIZE", "25")),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "20"))
configured_email_backend = os.getenv("EMAIL_BACKEND", "").strip()
if configured_email_backend:
    EMAIL_BACKEND = configured_email_backend
elif EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@example.com")

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "15"))
FREE_PLAN_DAILY_FILE_LIMIT = int(os.getenv("FREE_PLAN_DAILY_FILE_LIMIT", "5"))
FREE_PLAN_DAILY_NUMBER_LIMIT = int(os.getenv("FREE_PLAN_DAILY_NUMBER_LIMIT", "500"))
PRO_PLAN_DAILY_FILE_LIMIT = int(os.getenv("PRO_PLAN_DAILY_FILE_LIMIT", "0"))
PRO_PLAN_DAILY_NUMBER_LIMIT = int(os.getenv("PRO_PLAN_DAILY_NUMBER_LIMIT", "0"))
UPLOAD_PROCESSING_TIMEOUT_SECONDS = int(
    os.getenv("UPLOAD_PROCESSING_TIMEOUT_SECONDS", "180" if DJANGO_ENV == "production" else "600")
)

ADMIN_SITE_HEADER = "Number Extractor Administration"
ADMIN_SITE_TITLE = "Number Extractor Admin"
ADMIN_INDEX_TITLE = "Platform Operations"

USE_X_FORWARDED_HOST = env_bool("DJANGO_USE_X_FORWARDED_HOST", default=DJANGO_ENV == "production")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=DJANGO_ENV == "production")
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", default=DJANGO_ENV == "production")
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", default=DJANGO_ENV == "production")
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000" if DJANGO_ENV == "production" else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=DJANGO_ENV == "production",
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "same-origin"
