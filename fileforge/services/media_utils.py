"""
fileforge/services/media_utils.py

Low-bandwidth helpers: image compression, metadata extraction, thumbnail generation.
"""

import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)

MAX_IMAGE_DIMENSION = 2048  # px
JPEG_QUALITY = 82
THUMBNAIL_SIZE = (400, 400)


def compress_image(file_obj, filename: str) -> tuple[io.BytesIO, str]:
    """
    Compress an image file, resize if too large, and convert to JPEG.
    Returns (BytesIO, new_filename).
    """
    try:
        img = Image.open(file_obj)

        # Convert to RGB (handles PNG with alpha, etc.)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Resize if oversized
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.LANCZOS)
            logger.info("Resized image to %s", img.size)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        output.seek(0)

        # Rename to .jpg
        base = filename.rsplit(".", 1)[0]
        new_name = f"{base}.jpg"
        return output, new_name

    except Exception as exc:
        logger.warning("Image compression failed (%s), using original: %s", filename, exc)
        file_obj.seek(0)
        return file_obj, filename


def generate_thumbnail(file_obj, filename: str) -> tuple[io.BytesIO, str]:
    """Generate a small square thumbnail for cover images."""
    try:
        img = Image.open(file_obj)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Center-crop to square then resize
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))
        img.thumbnail(THUMBNAIL_SIZE, Image.LANCZOS)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=75, optimize=True)
        output.seek(0)

        base = filename.rsplit(".", 1)[0]
        thumb_name = f"{base}_thumb.jpg"
        return output, thumb_name

    except Exception as exc:
        logger.warning("Thumbnail generation failed: %s", exc)
        return None, None


def extract_audio_metadata(file_path: str) -> dict:
    """
    Extract duration and format info from an audio file using mutagen.
    Returns a dict with keys: duration_seconds, bitrate, format.
    """
    try:
        import mutagen
        audio = mutagen.File(file_path, easy=True)
        if audio is None:
            return {}
        return {
            "duration_seconds": int(audio.info.length) if hasattr(audio, "info") else None,
            "bitrate": getattr(audio.info, "bitrate", None),
            "format": type(audio).__name__,
        }
    except Exception as exc:
        logger.warning("Audio metadata extraction failed: %s", exc)
        return {}