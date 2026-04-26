"""
fileforge/serializers.py
"""

from rest_framework import serializers
from .models import DriveFile

ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/wav", "audio/ogg", "audio/flac", "audio/mp4"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_AUDIO_SIZE = 200 * 1024 * 1024   # 200 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024    # 10 MB


class DriveFileSerializer(serializers.ModelSerializer):
    size_mb = serializers.ReadOnlyField()
    stream_url = serializers.ReadOnlyField()
    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)

    class Meta:
        model = DriveFile
        fields = [
            "id",
            "name",
            "file_id",
            "folder_id",
            "category",
            "file_type",
            "size",
            "size_mb",
            "url",
            "stream_url",
            "uploaded_by",
            "uploaded_by_username",
            "resource_type",
            "resource_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "file_id", "folder_id", "file_type", "size",
            "url", "created_at", "updated_at",
        ]


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    category = serializers.ChoiceField(choices=DriveFile.Category.choices)
    resource_type = serializers.ChoiceField(choices=DriveFile.ResourceType.choices)
    resource_id = serializers.CharField(max_length=256)

    def validate(self, attrs):
        file = attrs["file"]
        category = attrs["category"]
        import mimetypes
        mime, _ = mimetypes.guess_type(file.name)
        mime = mime or "application/octet-stream"

        is_audio = category == DriveFile.Category.TRACK_AUDIO
        if is_audio:
            if mime not in ALLOWED_AUDIO_TYPES:
                raise serializers.ValidationError(
                    f"Unsupported audio type '{mime}'. Allowed: {ALLOWED_AUDIO_TYPES}"
                )
            if file.size > MAX_AUDIO_SIZE:
                raise serializers.ValidationError(
                    f"Audio file too large ({file.size / 1e6:.1f} MB). Max: {MAX_AUDIO_SIZE // 1e6} MB"
                )
        else:
            if mime not in ALLOWED_IMAGE_TYPES:
                raise serializers.ValidationError(
                    f"Unsupported image type '{mime}'. Allowed: {ALLOWED_IMAGE_TYPES}"
                )
            if file.size > MAX_IMAGE_SIZE:
                raise serializers.ValidationError(
                    f"Image too large ({file.size / 1e6:.1f} MB). Max: {MAX_IMAGE_SIZE // 1e6} MB"
                )

        attrs["_mime_type"] = mime
        return attrs


class FileUpdateSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    name = serializers.CharField(max_length=512, required=False)