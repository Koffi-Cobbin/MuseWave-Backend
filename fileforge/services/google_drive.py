"""
fileforge/services/google_drive.py

All Google Drive operations via a service account.
Handles upload, retrieval, update, deletion, and streaming.
"""

import io
import logging
import mimetypes
import os
from functools import lru_cache
from typing import Generator

from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]
CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB chunks for streaming


# ─── Auth ──────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_drive_service():
    """Build and cache a Drive API client using service account credentials."""
    cred_file = getattr(settings, "GOOGLE_SERVICE_ACCOUNT_FILE", None)
    if not cred_file or not os.path.exists(cred_file):
        raise EnvironmentError(
            "GOOGLE_SERVICE_ACCOUNT_FILE is not set or file does not exist. "
            "Set it in your .env / Django settings."
        )
    credentials = service_account.Credentials.from_service_account_file(
        cred_file, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


# ─── Upload ────────────────────────────────────────────────────────────────────

def upload_file(
    file_obj,
    filename: str,
    category: str,
    resource_type: str,
    resource_id: str,
    uploaded_by=None,
) -> "DriveFile":
    """
    Upload *file_obj* to the correct Drive folder for *category*.
    Creates and returns a DriveFile instance (not yet saved — caller saves it).

    filename should already be prefixed, e.g. track_{id}_audio.mp3
    """
    from fileforge.models import DriveFile
    from fileforge.services.folder_manager import get_folder_id

    service = get_drive_service()
    folder_id = get_folder_id(category)

    mime_type, _ = mimetypes.guess_type(filename)
    mime_type = mime_type or "application/octet-stream"

    # Ensure we can seek to measure size
    if hasattr(file_obj, "seek"):
        file_obj.seek(0, 2)
        file_size = file_obj.tell()
        file_obj.seek(0)
    else:
        content = file_obj.read()
        file_size = len(content)
        file_obj = io.BytesIO(content)

    metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaIoBaseUpload(file_obj, mimetype=mime_type, chunksize=CHUNK_SIZE, resumable=True)

    drive_file = (
        service.files()
        .create(
            body=metadata,
            media_body=media,
            fields="id, name, webContentLink, webViewLink",
        )
        .execute()
    )

    file_id = drive_file["id"]

    # Make the file readable by anyone with the link (for proxy streaming via service account)
    # We keep files private; the backend proxies them, so no public permission needed.
    # If you want direct links: uncomment below.
    # service.permissions().create(
    #     fileId=file_id, body={"type": "anyone", "role": "reader"}
    # ).execute()

    logger.info("Uploaded '%s' to Drive (file_id=%s, folder=%s)", filename, file_id, folder_id)

    drive_record = DriveFile(
        name=filename,
        file_id=file_id,
        folder_id=folder_id,
        category=category,
        file_type=mime_type,
        size=file_size,
        url=f"/api/fileforge/files/{{}}/stream/",  # placeholder; filled after save
        resource_type=resource_type,
        resource_id=str(resource_id),
        uploaded_by=uploaded_by,
    )
    drive_record.save()
    # Update url to include the real UUID
    drive_record.url = f"/api/fileforge/files/{drive_record.id}/stream/"
    drive_record.save(update_fields=["url"])

    return drive_record


# ─── Get metadata ──────────────────────────────────────────────────────────────

def get_file(file_id: str) -> dict:
    """Return Drive metadata for *file_id*."""
    service = get_drive_service()
    return (
        service.files()
        .get(fileId=file_id, fields="id, name, mimeType, size, webContentLink, webViewLink")
        .execute()
    )


# ─── Update ────────────────────────────────────────────────────────────────────

def update_file(file_id: str, file_obj=None, filename: str = None, metadata: dict = None) -> dict:
    """
    Update Drive file content and/or metadata.
    Returns updated Drive metadata dict.
    """
    service = get_drive_service()

    body = metadata or {}
    if filename:
        body["name"] = filename

    if file_obj is not None:
        mime_type, _ = mimetypes.guess_type(filename or "file")
        mime_type = mime_type or "application/octet-stream"
        media = MediaIoBaseUpload(file_obj, mimetype=mime_type, chunksize=CHUNK_SIZE, resumable=True)
        result = (
            service.files()
            .update(fileId=file_id, body=body, media_body=media, fields="id, name, webContentLink")
            .execute()
        )
    else:
        result = (
            service.files()
            .update(fileId=file_id, body=body, fields="id, name, webContentLink")
            .execute()
        )

    logger.info("Updated Drive file file_id=%s", file_id)
    return result


# ─── Delete ────────────────────────────────────────────────────────────────────

def delete_file(file_id: str) -> None:
    """Permanently delete a file from Drive."""
    service = get_drive_service()
    service.files().delete(fileId=file_id).execute()
    logger.info("Deleted Drive file file_id=%s", file_id)


# ─── Streaming ─────────────────────────────────────────────────────────────────

def stream_file_chunks(file_id: str, start: int = 0, end: int = None) -> Generator[bytes, None, None]:
    """
    Generator that yields byte chunks for the given Drive file.
    Supports Range requests (start/end byte positions).
    Uses service account credentials for authenticated download.
    """
    service = get_drive_service()

    # Get file size first
    meta = service.files().get(fileId=file_id, fields="size, mimeType").execute()
    total_size = int(meta.get("size", 0))
    if end is None or end >= total_size:
        end = total_size - 1

    request = service.files().get_media(fileId=file_id)

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request, chunksize=CHUNK_SIZE)

    bytes_yielded = 0
    done = False

    while not done:
        status, done = downloader.next_chunk()
        buffer.seek(0)
        chunk = buffer.read()
        buffer.seek(0)
        buffer.truncate(0)

        chunk_start = bytes_yielded
        chunk_end = bytes_yielded + len(chunk) - 1

        # Slice chunk to honor Range header
        if chunk_end < start:
            bytes_yielded += len(chunk)
            continue
        if chunk_start > end:
            return

        slice_start = max(0, start - chunk_start)
        slice_end = min(len(chunk), end - chunk_start + 1)
        yield chunk[slice_start:slice_end]
        bytes_yielded += len(chunk)


def generate_stream_url(file_id: str) -> str:
    """Return the proxy streaming URL for a Drive file (preferred over webContentLink)."""
    from fileforge.models import DriveFile
    try:
        record = DriveFile.objects.get(file_id=file_id)
        return f"/api/fileforge/files/{record.id}/stream/"
    except DriveFile.DoesNotExist:
        return f"/api/fileforge/stream/drive/{file_id}/"