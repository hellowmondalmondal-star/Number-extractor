from django.urls import path

from apps.dashboard.views import AdminViewSet, DashboardViewSet

urlpatterns = [
    path("dashboard/me", DashboardViewSet.as_view({"get": "me"}), name="dashboard-me"),
    path("dashboard/activity", DashboardViewSet.as_view({"get": "activity"}), name="dashboard-activity"),
    path("admin/users", AdminViewSet.as_view({"get": "users"}), name="admin-users"),
    path("admin/stats", AdminViewSet.as_view({"get": "stats"}), name="admin-stats"),
    path("admin/activity", AdminViewSet.as_view({"get": "activity"}), name="admin-activity"),
]
