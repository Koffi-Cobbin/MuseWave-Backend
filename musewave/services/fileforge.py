"""
FileForge client for MuseWave.

Base URL  : configured via settings.FILEFORGE_BASE_URL
Auth      : Bearer token from settings.FILEFORGE_API_KEY

Public API
----------
upload_file(file_obj, filename, provider=None) -> dict
    Upload a file to FileForge in sync mode.
    Returns the full FileForge file record, e.g.:
        {"id": 42, "url": "https://...", "status": "completed", ...}

delete_file(fileforge_id) -> None
    Delete a file from FileForge (and from the underlying provider).
    Silently ignores 404 responses.

health() -> dict
    Ping /api/health/ — useful for connectivity checks.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 60  # seconds


def _base_url():
    return getattr(settings, "FILEFORGE_BASE_URL", "https://fileforge1.pythonanywhere.com")


def _headers():
    api_key = getattr(settings, "FILEFORGE_API_KEY", "")
    return {"Authorization": f"Bearer {api_key}"}


def health():
    """GET /api/health/ — no auth required."""
    resp = requests.get(f"{_base_url()}/api/health/", timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def upload_file(file_obj, filename, provider=None):
    """
    Upload *file_obj* to FileForge using sync mode.

    Parameters
    ----------
    file_obj : file-like object
        An open binary stream or a Django InMemoryUploadedFile.
    filename : str
        Desired filename on the provider.
    provider : str | None
        Provider name (e.g. "cloudinary"). Defaults to the server-side
        default when omitted.

    Returns
    -------
    dict
        Full FileForge file record.  Key fields: ``id``, ``url``, ``status``.

    Raises
    ------
    FileForgeError
        Wraps any HTTP or connectivity error.
    """
    url = f"{_base_url()}/api/files/"
    data = {"name": filename, "mode": "sync"}
    if provider:
        data["provider"] = provider

    try:
        file_obj.seek(0)
    except (AttributeError, Exception):
        pass

    try:
        resp = requests.post(
            url,
            headers=_headers(),
            data=data,
            files={"file": (filename, file_obj)},
            timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise FileForgeError(f"Connection error uploading to FileForge: {exc}") from exc

    if resp.status_code not in (200, 201, 202):
        raise FileForgeError(
            f"FileForge upload failed ({resp.status_code}): {resp.text[:300]}"
        )

    record = resp.json()
    if isinstance(record, dict) and record.get("file"):
        record = record["file"]

    return record


def delete_file(fileforge_id):
    """
    DELETE /api/files/{id}/ — removes the record and the underlying provider file.

    Silently ignores 404 (already gone). Raises FileForgeError on other errors.
    """
    url = f"{_base_url()}/api/files/{fileforge_id}/"
    try:
        resp = requests.delete(url, headers=_headers(), timeout=_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("FileForge delete request failed for id=%s: %s", fileforge_id, exc)
        return

    if resp.status_code == 404:
        logger.debug("FileForge file %s not found (already deleted).", fileforge_id)
        return

    if resp.status_code not in (200, 204):
        logger.warning(
            "FileForge delete returned %s for id=%s: %s",
            resp.status_code, fileforge_id, resp.text[:200],
        )


class FileForgeError(Exception):
    """Raised when a FileForge API call fails."""
