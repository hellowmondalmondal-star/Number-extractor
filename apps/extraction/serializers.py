from rest_framework import serializers

from apps.extraction.models import ExtractionResult


class ExtractionResultSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    upload_id = serializers.UUIDField(source="upload.id", read_only=True)
    upload_name = serializers.CharField(source="upload.original_name", read_only=True)

    class Meta:
        model = ExtractionResult
        fields = (
            "id",
            "upload_id",
            "upload_name",
            "numbers",
            "total_numbers",
            "created_at",
            "updated_at",
            "download_url",
        )
        read_only_fields = fields

    def get_download_url(self, obj):
        request = self.context.get("request")
        if not obj.result_file:
            return None
        url = f"/api/download/{obj.id}"
        return request.build_absolute_uri(url) if request else url
