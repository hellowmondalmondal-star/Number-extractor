from rest_framework import mixins, permissions, viewsets

from apps.dashboard.services import log_activity
from apps.uploads.models import UploadedFile
from apps.uploads.permissions import IsOwnerOrAdmin
from apps.uploads.serializers import UploadCreateSerializer, UploadSerializer


class UploadViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    queryset = UploadedFile.objects.select_related("user").all()

    def get_queryset(self):
        queryset = self.queryset.select_related("extraction_result")
        if self.request.user.is_admin:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return UploadCreateSerializer
        return UploadSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def perform_create(self, serializer):
        uploaded_file = serializer.save()
        log_activity(
            user=self.request.user,
            action="file_uploaded",
            description=f"Uploaded {uploaded_file.original_name}.",
            metadata={"upload_id": str(uploaded_file.id), "file_type": uploaded_file.file_type},
        )
