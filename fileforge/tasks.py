"""
fileforge/tasks.py

Django-Q2 background tasks for async file processing.
Replaces the previous Celery implementation — no broker/Redis required.

Enqueue tasks with:
    from django_q.tasks import async_task
    async_task('fileforge.tasks.upload_file_async', ...)
"""

import logging
import os

logger = logging.getLogger(__name__)


def upload_file_async(
    file_path: str,
    filename: str,
    category: str,
    resource_type: str,
    resource_id: str,
    user_id=None,
):
    """
    Upload a file to Google Drive.
    *file_path* is a path to a temp file written by the view.

    Called asynchronously via Django-Q2:
        async_task('fileforge.tasks.upload_file_async', ...)
    """
    from fileforge.services.google_drive import upload_file
    from fileforge.services.media_utils import compress_image

    try:
        with open(file_path, "rb") as f:
            # Compress images before upload
            if category in ("track_cover", "album_cover", "user_avatar"):
                f, filename = compress_image(f, filename)

            user = None
            if user_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.filter(pk=user_id).first()

            drive_file = upload_file(
                file_obj=f,
                filename=filename,
                category=category,
                resource_type=resource_type,
                resource_id=resource_id,
                uploaded_by=user,
            )

        logger.info("Async upload complete: DriveFile id=%s", drive_file.id)
        return str(drive_file.id)

    except Exception as exc:
        logger.error("Async upload failed: %s", exc, exc_info=True)
        raise  # Django-Q2 will record the failure and retry per Q_CLUSTER settings

    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass


def extract_and_store_audio_metadata(drive_file_id: str, file_path: str):
    """
    Extract audio metadata (duration, bitrate) from a temp file
    and store it on the related Track model.

    Called asynchronously via Django-Q2:
        async_task('fileforge.tasks.extract_and_store_audio_metadata', ...)
    """
    from fileforge.models import DriveFile
    from fileforge.services.media_utils import extract_audio_metadata

    try:
        meta = extract_audio_metadata(file_path)
        if not meta:
            return

        drive_file = DriveFile.objects.get(id=drive_file_id)
        if drive_file.resource_type == "track":
            from musewave.models import Track
            Track.objects.filter(pk=drive_file.resource_id).update(
                audio_duration=meta.get("duration_seconds"),
            )
            logger.info("Stored audio metadata for Track %s", drive_file.resource_id)

    except Exception as exc:
        logger.error("Metadata extraction failed: %s", exc, exc_info=True)
        raise

    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass


def generate_and_upload_thumbnail(drive_file_id: str, resource_type: str, resource_id: str):
    """
    Download a cover image from Drive, generate a thumbnail, re-upload it.

    Called asynchronously via Django-Q2:
        async_task('fileforge.tasks.generate_and_upload_thumbnail', ...)
    """
    from fileforge.models import DriveFile
    from fileforge.services.google_drive import get_drive_service, upload_file
    from fileforge.services.media_utils import generate_thumbnail
    import io
    from googleapiclient.http import MediaIoBaseDownload

    try:
        drive_file = DriveFile.objects.get(id=drive_file_id)
        service = get_drive_service()

        # Download original
        request = service.files().get_media(fileId=drive_file.file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buf.seek(0)

        thumb_io, thumb_name = generate_thumbnail(buf, drive_file.name)
        if thumb_io is None:
            return

        upload_file(
            file_obj=thumb_io,
            filename=thumb_name,
            category=drive_file.category,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        logger.info("Thumbnail uploaded for DriveFile %s", drive_file_id)

    except Exception as exc:
        logger.error("Thumbnail generation failed: %s", exc, exc_info=True)
        raise