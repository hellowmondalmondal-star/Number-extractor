from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.views.generic import TemplateView
from rest_framework import permissions, response, viewsets

from apps.accounts.permissions import IsAdminUserRole
from apps.dashboard.models import ActivityLog
from apps.dashboard.serializers import ActivityLogSerializer, AdminUserSerializer
from apps.dashboard.services import build_admin_stats
from apps.extraction.models import ExtractionResult
from apps.extraction.serializers import ExtractionResultSerializer
from apps.subscriptions.serializers import UserSubscriptionSerializer
from apps.subscriptions.services import get_or_create_user_subscription
from apps.uploads.models import UploadedFile
from apps.uploads.serializers import UploadSerializer

User = get_user_model()


class DashboardHomeView(TemplateView):
    template_name = "dashboard/index.html"


class DashboardAppView(TemplateView):
    template_name = "dashboard/app.html"


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def me(self, request):
        uploads = UploadedFile.objects.filter(user=request.user).select_related("user", "extraction_result")[:5]
        results = ExtractionResult.objects.filter(user=request.user).select_related("upload")[:5]
        stats = {
            "uploads": UploadedFile.objects.filter(user=request.user).count(),
            "results": ExtractionResult.objects.filter(user=request.user).count(),
            "numbers_extracted": ExtractionResult.objects.filter(user=request.user).aggregate(
                total=Sum("total_numbers")
            )["total"]
            or 0,
        }
        payload = {
            "stats": stats,
            "subscription": UserSubscriptionSerializer(get_or_create_user_subscription(request.user)).data,
            "recent_uploads": UploadSerializer(uploads, many=True, context={"request": request}).data,
            "recent_results": ExtractionResultSerializer(results, many=True, context={"request": request}).data,
        }
        return response.Response(payload)

    def activity(self, request):
        queryset = ActivityLog.objects.filter(user=request.user)[:50]
        return response.Response(ActivityLogSerializer(queryset, many=True).data)


class AdminViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def users(self, request):
        queryset = (
            User.objects.select_related("subscription__plan")
            .annotate(upload_count=Count("uploads", distinct=True), result_count=Count("results", distinct=True))
            .order_by("-date_joined")
        )
        return response.Response(AdminUserSerializer(queryset, many=True).data)

    def stats(self, request):
        return response.Response(build_admin_stats())

    def activity(self, request):
        queryset = ActivityLog.objects.select_related("user")[:100]
        return response.Response(ActivityLogSerializer(queryset, many=True).data)
