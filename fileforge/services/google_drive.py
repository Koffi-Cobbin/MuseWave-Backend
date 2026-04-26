"""
fileforge/services/google_drive.py

All Google Drive operations via OAuth2 (refresh token).
Uploads files to the authenticated user's personal Google Drive.
Handles upload, retrieval, update, deletion, and streaming.
"""

import io
import logging
import mimetypes
import os
from typing import Generator

from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]
CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB chunks for streaming


# ─── Auth ──────────────────────────────────────────────────────────────────────

def get_drive_service():
    """
    Build a Drive API client using OAuth2 refresh token credentials.
    The access token is refreshed automatically when expired.

    Requires in settings (loaded from .env):
        GOOGLE_CLIENT_ID
        GOOGLE_CLIENT_SECRET
        GOOGLE_REFRESH_TOKEN

    To generate these values, run:
        python generate_google_token.py
    """
    client_id     = getattr(settings, "GOOGLE_CLIENT_ID", None)
    client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", None)
    refresh_token = getattr(settings, "GOOGLE_REFRESH_TOKEN", None)

    if not all([client_id, client_secret, refresh_token]):
        raise EnvironmentError(
            "Missing Google OAuth2 credentials. "
            "Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN in your .env."
        )

    credentials = Credentials(
        token=None,  # will be fetched automatically on first API call
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
    )

    # Proactively refresh so we catch credential errors early
    if not credentials.valid:
        credentials.refresh(Request())

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
    Creates and returns a saved DriveFile instance.

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

    # Files are kept private; the backend proxies streams via the OAuth token.
    # To allow direct public links instead, uncomment:
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
    Uses OAuth2 credentials for authenticated download.
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