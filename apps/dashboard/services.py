from django.db.models import Sum

from apps.dashboard.models import ActivityLog
from apps.extraction.models import ExtractionResult
from apps.uploads.models import UploadedFile


def log_activity(user, action, description="", metadata=None):
    return ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        metadata=metadata or {},
    )


def build_admin_stats():
    from django.contrib.auth import get_user_model

    User = get_user_model()

    total_numbers = ExtractionResult.objects.aggregate(total=Sum("total_numbers"))["total"] or 0
    return {
        "total_users": User.objects.count(),
        "total_admins": User.objects.filter(role="admin").count(),
        "total_agents": User.objects.filter(role="agent").count(),
        "total_uploads": UploadedFile.objects.count(),
        "completed_uploads": UploadedFile.objects.filter(status="completed").count(),
        "failed_uploads": UploadedFile.objects.filter(status="failed").count(),
        "total_results": ExtractionResult.objects.count(),
        "total_numbers_extracted": total_numbers,
        "recent_activity_count": ActivityLog.objects.count(),
    }
