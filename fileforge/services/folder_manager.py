"""
fileforge/services/folder_manager.py

Ensures the MuseWave folder structure exists in the admin Google Drive account.
Caches folder IDs in the database (DriveFolder cache model) and in-memory.
"""

import logging
from django.core.cache import cache
from .google_drive import get_drive_service

logger = logging.getLogger(__name__)

# ─── Folder tree definition ────────────────────────────────────────────────────
FOLDER_TREE = {
    "root": {
        "name": "MuseWave",
        "children": {
            "Tracks": {
                "name": "Tracks",
                "children": {
                    "track_audio": {"name": "Audio"},
                    "track_cover": {"name": "Covers"},
                },
            },
            "Albums": {
                "name": "Albums",
                "children": {
                    "album_cover": {"name": "Covers"},
                },
            },
            "Users": {
                "name": "Users",
                "children": {
                    "user_avatar": {"name": "Avatars"},
                },
            },
        },
    }
}

CACHE_PREFIX = "fileforge:folder:"
CACHE_TTL = 60 * 60 * 24  # 24 hours

# In-process memory cache as a fast layer in front of Redis
_local_cache: dict[str, str] = {}


def _cache_key(label: str) -> str:
    return f"{CACHE_PREFIX}{label}"


def _get_cached(label: str) -> str | None:
    if label in _local_cache:
        return _local_cache[label]
    value = cache.get(_cache_key(label))
    if value:
        _local_cache[label] = value
    return value


def _set_cached(label: str, folder_id: str) -> None:
    _local_cache[label] = folder_id
    cache.set(_cache_key(label), folder_id, CACHE_TTL)


def _find_or_create_folder(service, name: str, parent_id: str) -> str:
    """Return the Drive folder ID for *name* inside *parent_id*, creating it if absent."""
    query = (
        f"mimeType='application/vnd.google-apps.folder' "
        f"and name='{name}' "
        f"and '{parent_id}' in parents "
        f"and trashed=false"
    )
    results = (
        service.files()
        .list(q=query, fields="files(id, name)", spaces="drive")
        .execute()
    )
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    # Create the folder
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    logger.info("Created Drive folder '%s' (id=%s) under parent=%s", name, folder["id"], parent_id)
    return folder["id"]


def ensure_base_structure() -> dict[str, str]:
    """
    Walk the FOLDER_TREE and ensure every folder exists in Drive.
    Returns a mapping of category label → Drive folder ID.
    """
    from django.conf import settings

    service = get_drive_service()
    root_parent = getattr(settings, "GOOGLE_DRIVE_ROOT_FOLDER_ID", "root")

    folder_ids: dict[str, str] = {}

    # MuseWave root
    mw_cached = _get_cached("musewave_root")
    if mw_cached:
        musewave_id = mw_cached
    else:
        musewave_id = _find_or_create_folder(service, "MuseWave", root_parent)
        _set_cached("musewave_root", musewave_id)
    folder_ids["musewave_root"] = musewave_id

    # Second-level: Tracks, Albums, Users
    for section_key, section in FOLDER_TREE["root"]["children"].items():
        sec_cached = _get_cached(section_key)
        if sec_cached:
            section_id = sec_cached
        else:
            section_id = _find_or_create_folder(service, section["name"], musewave_id)
            _set_cached(section_key, section_id)
        folder_ids[section_key] = section_id

        # Third-level: Audio, Covers, Avatars (keyed by category string)
        for cat_key, cat in section.get("children", {}).items():
            cat_cached = _get_cached(cat_key)
            if cat_cached:
                cat_id = cat_cached
            else:
                cat_id = _find_or_create_folder(service, cat["name"], section_id)
                _set_cached(cat_key, cat_id)
            folder_ids[cat_key] = cat_id

    return folder_ids


def get_folder_id(category: str) -> str:
    """
    Return the Google Drive folder ID for the given category string.
    Calls ensure_base_structure if the folder ID is not cached.
    """
    cached = _get_cached(category)
    if cached:
        return cached

    folder_ids = ensure_base_structure()
    folder_id = folder_ids.get(category)
    if not folder_id:
        raise ValueError(f"Unknown category '{category}'. Valid: {list(folder_ids.keys())}")
    return folder_id