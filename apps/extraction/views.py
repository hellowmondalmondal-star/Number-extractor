from pathlib import Path

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, permissions, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.dashboard.services import log_activity
from apps.extraction.models import ExtractionResult
from apps.extraction.serializers import ExtractionResultSerializer
from apps.extraction.services import process_uploaded_file
from apps.uploads.models import UploadedFile
from apps.uploads.services import mark_stale_processing_upload


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
        with transaction.atomic():
            uploaded_file = get_object_or_404(
                UploadedFile.objects.select_for_update().select_related("user"),
                pk=file_id,
            )
            if not (request.user.is_admin or uploaded_file.user_id == request.user.id):
                raise PermissionDenied("You can only process your own uploads.")

            mark_stale_processing_upload(uploaded_file)
            try:
                existing_result = uploaded_file.extraction_result
            except UploadedFile.extraction_result.RelatedObjectDoesNotExist:
                existing_result = None

            if uploaded_file.status == UploadedFile.StatusChoices.PROCESSING:
                raise ValidationError("This file is already processing. Please wait for it to finish.")

            # Reuse the existing result when a queued duplicate request lands after the
            # first extraction already completed.
            if uploaded_file.status == UploadedFile.StatusChoices.COMPLETED and existing_result:
                serializer = self.get_serializer(existing_result)
                return Response(serializer.data)

            uploaded_file.status = UploadedFile.StatusChoices.PROCESSING
            uploaded_file.processed_at = timezone.now()
            uploaded_file.error_message = ""
            uploaded_file.save(update_fields=["status", "processed_at", "error_message"])

        try:
            result = process_uploaded_file(uploaded_file)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages) from exc
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
