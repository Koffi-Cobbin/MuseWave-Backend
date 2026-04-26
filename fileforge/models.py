import uuid
from django.db import models
from django.conf import settings


class DriveFile(models.Model):
    class Category(models.TextChoices):
        TRACK_AUDIO = "track_audio", "Track Audio"
        TRACK_COVER = "track_cover", "Track Cover"
        ALBUM_COVER = "album_cover", "Album Cover"
        USER_AVATAR = "user_avatar", "User Avatar"

    class ResourceType(models.TextChoices):
        TRACK = "track", "Track"
        ALBUM = "album", "Album"
        USER = "user", "User"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512)
    file_id = models.CharField(max_length=256, unique=True, help_text="Google Drive file ID")
    folder_id = models.CharField(max_length=256, help_text="Google Drive folder ID")
    category = models.CharField(max_length=20, choices=Category.choices)
    file_type = models.CharField(max_length=100, help_text="MIME type")
    size = models.BigIntegerField(default=0, help_text="File size in bytes")
    url = models.URLField(max_length=1024, blank=True, help_text="Proxy or direct URL")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_files",
    )
    resource_type = models.CharField(max_length=20, choices=ResourceType.choices)
    resource_id = models.CharField(max_length=256, help_text="ID of the related resource in Django DB")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["category"]),
            models.Index(fields=["file_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.category})"

    @property
    def stream_url(self):
        return f"/api/fileforge/files/{self.id}/stream/"

    @property
    def size_mb(self):
        return round(self.size / (1024 * 1024), 2)