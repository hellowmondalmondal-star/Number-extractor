from django.urls import path

from apps.extraction.views import ExtractionViewSet

urlpatterns = [
    path("process/<uuid:file_id>", ExtractionViewSet.as_view({"post": "process"}), name="process-upload"),
    path("results", ExtractionViewSet.as_view({"get": "list"}), name="result-list"),
    path("results/<uuid:pk>", ExtractionViewSet.as_view({"get": "retrieve"}), name="result-detail"),
    path("download/<uuid:result_id>", ExtractionViewSet.as_view({"get": "download"}), name="result-download"),
]
