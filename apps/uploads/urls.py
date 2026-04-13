from django.urls import path

from apps.uploads.views import UploadViewSet

urlpatterns = [
    path("upload", UploadViewSet.as_view({"post": "create"}), name="upload"),
    path("uploads", UploadViewSet.as_view({"get": "list"}), name="upload-list"),
    path("uploads/<uuid:pk>", UploadViewSet.as_view({"get": "retrieve"}), name="upload-detail"),
]
