from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.dashboard.services import log_activity
from apps.extraction.models import ExtractionResult
from apps.extraction.serializers import ExtractionResultSerializer
from apps.extraction.services import process_uploaded_file
from apps.uploads.models import UploadedFile


class ExtractionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ExtractionResultSerializer
    queryset = ExtractionResult.objects.select_related("user", "upload").all()

    def get_queryset(self):
        if self.request.user.is_admin:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def process(self, request, file_id):
        uploaded_file = get_object_or_404(UploadedFile.objects.select_related("user"), pk=file_id)
        if not (request.user.is_admin or uploaded_file.user_id == request.user.id):
            raise PermissionDenied("You can only process your own uploads.")

        result = process_uploaded_file(uploaded_file)
        serializer = self.get_serializer(result)
        return Response(serializer.data)

    def download(self, request, result_id):
        result = get_object_or_404(self.get_queryset(), pk=result_id)
        if not result.result_file:
            raise Http404("Result file not found.")

        log_activity(
            user=request.user,
            action="result_downloaded",
            description=f"Downloaded result for {result.upload.original_name}.",
            metadata={"result_id": str(result.id)},
        )

        return FileResponse(
            result.result_file.open("rb"),
            as_attachment=True,
            filename=Path(result.result_file.name).name,
        )
