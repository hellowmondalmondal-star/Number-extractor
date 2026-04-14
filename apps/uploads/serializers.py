from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.subscriptions.services import enforce_daily_file_limit
from apps.uploads.models import UploadedFile
from apps.uploads.services import detect_file_type, validate_file_object


class UploadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ("id", "file")
        read_only_fields = ("id",)

    def validate_file(self, value):
        return validate_file_object(value)

    def create(self, validated_data):
        user = self.context["request"].user
        file_obj = validated_data["file"]
        try:
            enforce_daily_file_limit(user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        return UploadedFile.objects.create(
            user=user,
            file=file_obj,
            original_name=file_obj.name,
            file_size=file_obj.size,
            file_type=detect_file_type(file_obj.name),
        )


class UploadSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    result_id = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = (
            "id",
            "original_name",
            "file_type",
            "file_size",
            "status",
            "upload_time",
            "processed_at",
            "error_message",
            "file_url",
            "result_id",
        )
        read_only_fields = fields

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return None
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_result_id(self, obj):
        try:
            result = obj.extraction_result
        except UploadedFile.extraction_result.RelatedObjectDoesNotExist:
            result = None
        return result.id if result else None
