from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from apps.dashboard.views import DashboardAppView, DashboardHomeView

admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="home"),
    path("app/", DashboardAppView.as_view(), name="app"),
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.subscriptions.urls")),
    path("api/", include("apps.uploads.urls")),
    path("api/", include("apps.extraction.urls")),
    path("api/", include("apps.dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
