"""
fileforge/views.py

DRF views for DriveFile CRUD + proxy streaming with HTTP Range support.
"""

import logging
import mimetypes
import os
import re
import tempfile

from django.http import StreamingHttpResponse, HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import DriveFile
from .serializers import DriveFileSerializer, FileUploadSerializer, FileUpdateSerializer
from .services.google_drive import (
    delete_file as drive_delete,
    get_file as drive_get,
    stream_file_chunks,
    update_file as drive_update,
    upload_file,
    get_drive_service,
)
from .services.media_utils import compress_image

logger = logging.getLogger(__name__)

LARGE_FILE_THRESHOLD = 10 * 1024 * 1024  # 10 MB — use async above this


def _build_filename(category: str, resource_id: str, original_name: str) -> str:
    """Prefix filename with category and resource ID for traceability."""
    ext = original_name.rsplit(".", 1)[-1] if "." in original_name else ""
    prefix_map = {
        DriveFile.Category.TRACK_AUDIO: f"track_{resource_id}_audio",
        DriveFile.Category.TRACK_COVER: f"track_{resource_id}_cover",
        DriveFile.Category.ALBUM_COVER: f"album_{resource_id}_cover",
        DriveFile.Category.USER_AVATAR: f"user_{resource_id}_avatar",
    }
    base = prefix_map.get(category, f"{category}_{resource_id}")
    return f"{base}.{ext}" if ext else base


class DriveFileViewSet(ModelViewSet):
    """
    CRUD for DriveFile records.

    POST   /api/fileforge/files/           → upload
    GET    /api/fileforge/files/           → list
    GET    /api/fileforge/files/{id}/      → retrieve
    PATCH  /api/fileforge/files/{id}/      → update
    DELETE /api/fileforge/files/{id}/      → delete
    GET    /api/fileforge/files/{id}/stream/ → proxy stream
    """

    queryset = DriveFile.objects.all()
    serializer_class = DriveFileSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        resource_type = self.request.query_params.get("resource_type")
        resource_id = self.request.query_params.get("resource_id")
        if category:
            qs = qs.filter(category=category)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if resource_id:
            qs = qs.filter(resource_id=resource_id)
        return qs

    # ── Upload ────────────────────────────────────────────────────────────────

    def create(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["file"]
        category = serializer.validated_data["category"]
        resource_type = serializer.validated_data["resource_type"]
        resource_id = serializer.validated_data["resource_id"]

        filename = _build_filename(category, resource_id, file.name)

        # Compress images synchronously (fast)
        if category in (
            DriveFile.Category.TRACK_COVER,
            DriveFile.Category.ALBUM_COVER,
            DriveFile.Category.USER_AVATAR,
        ):
            file, filename = compress_image(file, filename)

        # Large files → async; small files → synchronous
        if file.size > LARGE_FILE_THRESHOLD:
            return self._create_async(file, filename, category, resource_type, resource_id, request.user)

        drive_record = upload_file(
            file_obj=file,
            filename=filename,
            category=category,
            resource_type=resource_type,
            resource_id=resource_id,
            uploaded_by=request.user,
        )
        return Response(DriveFileSerializer(drive_record).data, status=status.HTTP_201_CREATED)

    def _create_async(self, file, filename, category, resource_type, resource_id, user):
        """Save file to temp disk and enqueue Celery task."""
        from .tasks import upload_file_async

        suffix = os.path.splitext(filename)[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        task = upload_file_async.delay(
            file_path=tmp_path,
            filename=filename,
            category=category,
            resource_type=resource_type,
            resource_id=str(resource_id),
            user_id=user.pk if user else None,
        )
        return Response(
            {"status": "queued", "task_id": task.id, "message": "Large file upload queued."},
            status=status.HTTP_202_ACCEPTED,
        )

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = FileUpdateSerializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data.get("file")
        new_name = serializer.validated_data.get("name")

        drive_update(
            file_id=instance.file_id,
            file_obj=file,
            filename=new_name or instance.name,
            metadata={"name": new_name} if new_name else None,
        )

        if new_name:
            instance.name = new_name
        if file:
            instance.size = file.size
        instance.save()

        return Response(DriveFileSerializer(instance).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # ── Delete ────────────────────────────────────────────────────────────────

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        drive_delete(instance.file_id)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Stream ────────────────────────────────────────────────────────────────

    @action(detail=True, methods=["get"], url_path="stream", permission_classes=[IsAuthenticated])
    def stream(self, request, pk=None):
        """
        Proxy stream a Drive file with HTTP Range support for seeking.
        """
        instance = self.get_object()
        file_id = instance.file_id

        # Get file size from Drive metadata
        meta = drive_get(file_id)
        total_size = int(meta.get("size", 0))
        mime_type = instance.file_type or "application/octet-stream"

        # Parse Range header
        range_header = request.META.get("HTTP_RANGE", "")
        start, end = 0, total_size - 1
        status_code = 200
        content_length = total_size

        if range_header:
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else total_size - 1
                end = min(end, total_size - 1)
                content_length = end - start + 1
                status_code = 206

        def file_iterator():
            yield from stream_file_chunks(file_id, start=start, end=end)

        response = StreamingHttpResponse(
            file_iterator(),
            status=status_code,
            content_type=mime_type,
        )
        response["Content-Length"] = content_length
        response["Accept-Ranges"] = "bytes"
        response["Content-Disposition"] = f'inline; filename="{instance.name}"'
        if status_code == 206:
            response["Content-Range"] = f"bytes {start}-{end}/{total_size}"

        return response


class TaskStatusView(APIView):
    """Poll Celery task status for async uploads."""

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        data = {
            "task_id": task_id,
            "status": result.status,
        }
        if result.ready():
            if result.successful():
                drive_file_id = result.result
                try:
                    df = DriveFile.objects.get(id=drive_file_id)
                    data["drive_file"] = DriveFileSerializer(df).data
                except DriveFile.DoesNotExist:
                    data["drive_file_id"] = drive_file_id
            else:
                data["error"] = str(result.result)
        return Response(data)