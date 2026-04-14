from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from apps.dashboard.services import log_activity
from config.settings import build_allowed_hosts, build_csrf_trusted_origins, build_database_config

User = get_user_model()


class SettingsResolutionTests(SimpleTestCase):
    def test_build_allowed_hosts_normalizes_urls_and_appends_render_hostname(self):
        allowed_hosts = build_allowed_hosts(
            configured_hosts=["https://portal.example.com", "http://localhost:8000"],
            site_url="https://portal.example.com",
            debug=False,
            render_external_hostname="number-extractor-2.onrender.com",
        )

        self.assertEqual(
            allowed_hosts,
            ["portal.example.com", "localhost", "number-extractor-2.onrender.com"],
        )

    def test_build_csrf_trusted_origins_uses_render_hostname_when_no_env_is_set(self):
        trusted_origins = build_csrf_trusted_origins(
            configured_origins=[],
            site_url="http://127.0.0.1:8000",
            debug=False,
            render_external_hostname="number-extractor-2.onrender.com",
        )

        self.assertEqual(trusted_origins, ["https://number-extractor-2.onrender.com"])

    def test_build_database_config_requires_database_url_in_production(self):
        with self.assertRaises(ImproperlyConfigured):
            build_database_config(database_url="", base_dir=Path("/tmp"), django_env="production")

    def test_build_database_config_rejects_sqlite_in_production(self):
        with self.assertRaises(ImproperlyConfigured):
            build_database_config(
                database_url="sqlite:////tmp/production.sqlite3",
                base_dir=Path("/tmp"),
                django_env="production",
            )

    def test_build_database_config_accepts_postgres_in_production(self):
        database_config = build_database_config(
            database_url="postgres://user:password@localhost:5432/number_extractor",
            base_dir=Path("/tmp"),
            django_env="production",
        )

        self.assertEqual(database_config["default"]["ENGINE"], "django.db.backends.postgresql")


class DashboardServiceTests(TestCase):
    def test_log_activity_creates_entry(self):
        user = User.objects.create_user(email="audit@example.com", full_name="Audit User", password="password123")
        entry = log_activity(user=user, action="unit_test", description="Created in test.")
        self.assertEqual(entry.user, user)
        self.assertEqual(entry.action, "unit_test")

    def test_home_page_renders(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_app_page_renders(self):
        response = self.client.get(reverse("app"))
        self.assertEqual(response.status_code, 200)
