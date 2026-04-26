import json
import logging

from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .models import User, Track, Like, Download, Play, Follow, Playlist, PlaylistTrack, Comment, Album

logger = logging.getLogger(__name__)


# ─── Shared Drive upload helper ───────────────────────────────────────────────

def _upload_to_drive(file_obj, category, resource_type, resource_id, user=None):
    """
    Upload *file_obj* to Google Drive under *category*.
    Returns a saved DriveFile instance, or raises serializers.ValidationError on failure.
    """
    from fileforge.models import DriveFile
    from fileforge.services.google_drive import upload_file as drive_upload
    from fileforge.services.media_utils import compress_image

    ext = file_obj.name.rsplit('.', 1)[-1] if '.' in file_obj.name else 'bin'

    prefix_map = {
        DriveFile.Category.TRACK_AUDIO: f"track_{resource_id}_audio",
        DriveFile.Category.TRACK_COVER: f"track_{resource_id}_cover",
        DriveFile.Category.ALBUM_COVER: f"album_{resource_id}_cover",
        DriveFile.Category.USER_AVATAR: f"user_{resource_id}_avatar",
        DriveFile.Category.USER_HEADER: f"user_{resource_id}_header",
    }
    filename = f"{prefix_map.get(category, f'{category}_{resource_id}')}.{ext}"

    # Compress images before uploading
    if category != DriveFile.Category.TRACK_AUDIO:
        file_obj, filename = compress_image(file_obj, filename)

    try:
        return drive_upload(
            file_obj=file_obj,
            filename=filename,
            category=category,
            resource_type=resource_type,
            resource_id=str(resource_id),
            uploaded_by=user,
        )
    except Exception as exc:
        logger.error("Drive upload failed (category=%s, resource=%s): %s", category, resource_id, exc)
        raise serializers.ValidationError(f"File upload failed: {exc}")


def _replace_drive_file(old_drive_file, new_file_obj, category, resource_type, resource_id, user=None):
    """
    Upload *new_file_obj* then delete the old DriveFile from Drive + DB.
    Returns the new DriveFile instance.
    """
    from fileforge.services.google_drive import delete_file as drive_delete

    new_drive_file = _upload_to_drive(new_file_obj, category, resource_type, resource_id, user)

    if old_drive_file:
        try:
            drive_delete(old_drive_file.file_id)
            old_drive_file.delete()
        except Exception as exc:
            logger.warning("Could not delete old DriveFile %s: %s", old_drive_file.id, exc)

    return new_drive_file


def _drive_url(drive_file, request=None):
    """Return an absolute stream URL for a DriveFile, or None."""
    if not drive_file:
        return None
    url = drive_file.stream_url          # e.g. /api/fileforge/files/<id>/stream/
    if request:
        return request.build_absolute_uri(url)
    return url


# ─── User serializers ─────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    """Read serializer — returns Drive-backed URLs for avatar and header."""
    social_links = serializers.SerializerMethodField()
    avatar_url   = serializers.SerializerMethodField()
    header_url   = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'display_name', 'bio',
            'avatar_url', 'header_url', 'location', 'website',
            'social_links', 'verified', 'created_at', 'updated_at',
        ]
        read_only_fields = fields   # strictly read-only; writes go through UpdateUserSerializer

    def get_avatar_url(self, obj):
        return _drive_url(obj.avatar_file, self.context.get('request'))

    def get_header_url(self, obj):
        return _drive_url(obj.header_file, self.context.get('request'))

    def get_social_links(self, obj):
        return {
            'twitter':    obj.twitter,
            'instagram':  obj.instagram,
            'spotify':    obj.spotify,
            'soundcloud': obj.soundcloud,
        }


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Safe public view — omits email and other sensitive fields.
    Used by the unauthenticated GET /api/users/<id> endpoint.
    """
    social_links = serializers.SerializerMethodField()
    avatar_url   = serializers.SerializerMethodField()
    header_url   = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'display_name', 'bio',
            'avatar_url', 'header_url', 'location', 'website',
            'social_links', 'verified', 'created_at',
        ]
        read_only_fields = fields

    def get_avatar_url(self, obj):
        return _drive_url(obj.avatar_file, self.context.get('request'))

    def get_header_url(self, obj):
        return _drive_url(obj.header_file, self.context.get('request'))

    def get_social_links(self, obj):
        return {
            'twitter':    obj.twitter,
            'instagram':  obj.instagram,
            'spotify':    obj.spotify,
            'soundcloud': obj.soundcloud,
        }


class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Write serializer for PATCH /api/users/<id>.
    Accepts optional avatar_file / header_file files and routes them to Drive.
    """
    avatar_file = serializers.ImageField(write_only=True, required=False, allow_null=True)
    header_file = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model  = User
        fields = [
            'display_name', 'bio', 'location', 'website',
            'twitter', 'instagram', 'spotify', 'soundcloud',
            'avatar_file', 'header_file',
        ]

    def update(self, instance, validated_data):
        from fileforge.models import DriveFile

        avatar_file = validated_data.pop('avatar_file', None)
        header_file = validated_data.pop('header_file', None)

        # Update plain fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if avatar_file:
            instance.avatar_file = _replace_drive_file(
                old_drive_file=instance.avatar_file,
                new_file_obj=avatar_file,
                category=DriveFile.Category.USER_AVATAR,
                resource_type=DriveFile.ResourceType.USER,
                resource_id=str(instance.id),
                user=instance,
            )
            instance.save(update_fields=['avatar_file'])

        if header_file:
            instance.header_file = _replace_drive_file(
                old_drive_file=instance.header_file,
                new_file_obj=header_file,
                category=DriveFile.Category.USER_HEADER,
                resource_type=DriveFile.ResourceType.USER,
                resource_id=str(instance.id),
                user=instance,
            )
            instance.save(update_fields=['header_file'])

        return instance


class CreateUserSerializer(serializers.ModelSerializer):
    twitter    = serializers.CharField(required=False, allow_blank=True)
    instagram  = serializers.CharField(required=False, allow_blank=True)
    spotify    = serializers.CharField(required=False, allow_blank=True)
    soundcloud = serializers.CharField(required=False, allow_blank=True)

    # Optional avatar on signup — uploaded to Drive
    avatar_file = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model  = User
        fields = [
            'username', 'email', 'password', 'display_name', 'bio',
            'location', 'website', 'twitter', 'instagram', 'spotify', 'soundcloud',
            'avatar_file',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'min_length': 3, 'max_length': 30},
            'bio':      {'max_length': 500},
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def create(self, validated_data):
        from fileforge.models import DriveFile

        password      = validated_data.pop('password')
        avatar_file = validated_data.pop('avatar_file', None)

        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.verified  = False
        user.save()

        if avatar_file:
            try:
                drive_file = _upload_to_drive(
                    file_obj=avatar_file,
                    category=DriveFile.Category.USER_AVATAR,
                    resource_type=DriveFile.ResourceType.USER,
                    resource_id=str(user.id),
                    user=user,
                )
                user.avatar_file = drive_file
                user.save(update_fields=['avatar_file'])
            except Exception as exc:
                logger.warning("Avatar upload failed during signup for %s: %s", user.email, exc)
                # Non-fatal — account is still created

        user._plain_password = password
        self.send_verification_email(user)
        return user

    def send_verification_email(self, user):
        try:
            token = default_token_generator.make_token(user)
            uid   = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"

            send_mail(
                subject='Verify Your MuseWave Account',
                message=f"""
Hello {user.display_name or user.username}!

Thank you for registering with MuseWave!

Verify your email address:

{verification_url}

This link will expire in 24 hours.

Best regards,
The MuseWave Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info("Verification email sent to %s", user.email)
        except Exception as exc:
            logger.error("Failed to send verification email to %s: %s", user.email, exc)


# ─── Album serializers ────────────────────────────────────────────────────────

class AlbumSerializer(serializers.ModelSerializer):
    user_id     = serializers.UUIDField(source='user.id', read_only=True)
    track_count = serializers.SerializerMethodField()
    cover_url   = serializers.SerializerMethodField()

    class Meta:
        model  = Album
        fields = [
            'id', 'user_id', 'title', 'artist', 'description',
            'cover_url', 'cover_gradient', 'release_date', 'genre',
            'published', 'created_at', 'updated_at', 'track_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_track_count(self, obj):
        return obj.tracks.count()

    def get_cover_url(self, obj):
        return _drive_url(obj.cover_file, self.context.get('request'))


class CreateAlbumSerializer(serializers.ModelSerializer):
    user_id      = serializers.UUIDField(write_only=True)
    cover_file = serializers.ImageField(write_only=True, required=False, allow_null=True)
    track_ids    = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model  = Album
        fields = [
            'user_id', 'title', 'artist', 'description',
            'cover_file', 'cover_gradient', 'release_date', 'genre',
            'published', 'track_ids',
        ]

    def create(self, validated_data):
        from fileforge.models import DriveFile

        cover_file   = validated_data.pop('cover_file', None)
        track_ids_raw  = validated_data.pop('track_ids', [])
        user_id        = validated_data.pop('user_id')

        if isinstance(track_ids_raw, str):
            try:
                track_ids = json.loads(track_ids_raw)
            except json.JSONDecodeError:
                track_ids = []
        else:
            track_ids = track_ids_raw

        user  = User.objects.get(id=user_id)
        album = Album.objects.create(user=user, **validated_data)

        if cover_file:
            try:
                drive_file = _upload_to_drive(
                    file_obj=cover_file,
                    category=DriveFile.Category.ALBUM_COVER,
                    resource_type=DriveFile.ResourceType.ALBUM,
                    resource_id=str(album.id),
                    user=user,
                )
                album.cover_file = drive_file
                album.save(update_fields=['cover_file'])
            except Exception as exc:
                album.delete()
                raise serializers.ValidationError(f"Cover upload failed: {exc}")

        if track_ids:
            Track.objects.filter(id__in=track_ids).update(album=album)

        return album


class UpdateAlbumSerializer(serializers.ModelSerializer):
    cover_file = serializers.ImageField(write_only=True, required=False, allow_null=True)
    track_ids    = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model  = Album
        fields = [
            'title', 'artist', 'description',
            'cover_file', 'cover_gradient', 'release_date', 'genre',
            'published', 'track_ids',
        ]

    def update(self, instance, validated_data):
        from fileforge.models import DriveFile

        cover_file  = validated_data.pop('cover_file', None)
        track_ids_raw = validated_data.pop('track_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if cover_file:
            instance.cover_file = _replace_drive_file(
                old_drive_file=instance.cover_file,
                new_file_obj=cover_file,
                category=DriveFile.Category.ALBUM_COVER,
                resource_type=DriveFile.ResourceType.ALBUM,
                resource_id=str(instance.id),
            )
            instance.save(update_fields=['cover_file'])

        if track_ids_raw is not None:
            if isinstance(track_ids_raw, str):
                try:
                    track_ids = json.loads(track_ids_raw)
                except json.JSONDecodeError:
                    track_ids = []
            else:
                track_ids = track_ids_raw
            # Disassociate tracks no longer in the list, associate new ones
            Track.objects.filter(album=instance).update(album=None)
            Track.objects.filter(id__in=track_ids).update(album=instance)

        return instance


# ─── Track serializers ────────────────────────────────────────────────────────

class TrackSerializer(serializers.ModelSerializer):
    user_id   = serializers.UUIDField(source='user.id', read_only=True)
    album_id  = serializers.UUIDField(source='album.id', read_only=True, allow_null=True)
    audio_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model  = Track
        fields = [
            'id', 'user_id', 'album_id', 'title', 'artist', 'artist_slug', 'description',
            'genre', 'mood', 'tags', 'audio_url', 'audio_file_size',
            'audio_duration', 'audio_format', 'cover_url', 'cover_gradient',
            'waveform_data', 'bpm', 'key', 'plays', 'likes', 'downloads',
            'shares', 'published', 'published_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'plays', 'likes', 'downloads', 'shares',
            'published_at', 'created_at', 'updated_at',
        ]

    def get_audio_url(self, obj):
        return _drive_url(obj.audio_file, self.context.get('request'))

    def get_cover_url(self, obj):
        return _drive_url(obj.cover_file, self.context.get('request'))


class CreateTrackSerializer(serializers.ModelSerializer):
    user_id      = serializers.UUIDField(write_only=True)
    audio_file   = serializers.FileField(write_only=True)
    cover_file   = serializers.ImageField(write_only=True, required=False, allow_null=True)
    tags         = serializers.JSONField(required=False)

    class Meta:
        model  = Track
        fields = [
            'user_id', 'title', 'artist', 'artist_slug', 'description',
            'genre', 'mood', 'tags', 'audio_file', 'audio_file_size',
            'audio_duration', 'audio_format', 'cover_file', 'cover_gradient',
            'waveform_data', 'bpm', 'key', 'published',
        ]

    def validate_audio_duration(self, value):
        if value is None or value <= 0:
            raise serializers.ValidationError("audio_duration must be a positive number.")
        return value

    def create(self, validated_data):
        from fileforge.models import DriveFile
        from django.utils import timezone

        user_id      = validated_data.pop('user_id')
        audio_file = validated_data.pop('audio_file')
        cover_file = validated_data.pop('cover_file', None)

        user = User.objects.get(id=user_id)

        if isinstance(validated_data.get('tags'), str):
            try:
                validated_data['tags'] = json.loads(validated_data['tags'])
            except json.JSONDecodeError:
                validated_data['tags'] = []

        if validated_data.get('published', False):
            validated_data['published_at'] = timezone.now()

        # Create track without files first (need its UUID for filenames)
        track = Track.objects.create(user=user, **validated_data)

        # ── Upload audio ──────────────────────────────────────────────────────
        try:
            audio_drive = _upload_to_drive(
                file_obj=audio_file,
                category=DriveFile.Category.TRACK_AUDIO,
                resource_type=DriveFile.ResourceType.TRACK,
                resource_id=str(track.id),
                user=user,
            )
            track.audio_file      = audio_drive
            track.audio_file_size = audio_drive.size
            if not track.audio_format:
                track.audio_format = (
                    audio_drive.file_type.split('/')[-1] if audio_drive.file_type else None
                )
            track.save(update_fields=['audio_file', 'audio_file_size', 'audio_format'])
        except Exception as exc:
            track.delete()
            raise serializers.ValidationError(f"Audio upload failed: {exc}")

        # ── Upload cover (non-fatal) ───────────────────────────────────────────
        if cover_file:
            try:
                cover_drive = _upload_to_drive(
                    file_obj=cover_file,
                    category=DriveFile.Category.TRACK_COVER,
                    resource_type=DriveFile.ResourceType.TRACK,
                    resource_id=str(track.id),
                    user=user,
                )
                track.cover_file = cover_drive
                track.save(update_fields=['cover_file'])
            except Exception as exc:
                logger.warning("Cover upload failed for track %s: %s", track.id, exc)

        return track


class UpdateTrackSerializer(serializers.ModelSerializer):
    audio_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    cover_file = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model  = Track
        fields = [
            'title', 'artist', 'artist_slug', 'description', 'genre', 'mood',
            'tags', 'audio_file', 'audio_file_size', 'audio_duration',
            'audio_format', 'cover_file', 'cover_gradient', 'waveform_data',
            'bpm', 'key', 'published',
        ]

    def update(self, instance, validated_data):
        from fileforge.models import DriveFile
        from django.utils import timezone

        audio_file = validated_data.pop('audio_file', None)
        cover_file = validated_data.pop('cover_file', None)

        if 'published' in validated_data and validated_data['published'] and not instance.published:
            instance.published_at = timezone.now()

        if isinstance(validated_data.get('tags'), str):
            try:
                validated_data['tags'] = json.loads(validated_data['tags'])
            except json.JSONDecodeError:
                pass

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ── Replace audio ─────────────────────────────────────────────────────
        if audio_file:
            new_audio = _replace_drive_file(
                old_drive_file=instance.audio_file,
                new_file_obj=audio_file,
                category=DriveFile.Category.TRACK_AUDIO,
                resource_type=DriveFile.ResourceType.TRACK,
                resource_id=str(instance.id),
            )
            instance.audio_file      = new_audio
            instance.audio_file_size = new_audio.size
            if not instance.audio_format:
                instance.audio_format = (
                    new_audio.file_type.split('/')[-1] if new_audio.file_type else None
                )
            instance.save(update_fields=['audio_file', 'audio_file_size', 'audio_format'])

        # ── Replace cover ─────────────────────────────────────────────────────
        if cover_file:
            new_cover = _replace_drive_file(
                old_drive_file=instance.cover_file,
                new_file_obj=cover_file,
                category=DriveFile.Category.TRACK_COVER,
                resource_type=DriveFile.ResourceType.TRACK,
                resource_id=str(instance.id),
            )
            instance.cover_file = new_cover
            instance.save(update_fields=['cover_file'])

        return instance


# ─── Remaining serializers (unchanged logic, kept for completeness) ───────────

class LikeSerializer(serializers.ModelSerializer):
    user_id  = serializers.UUIDField(source='user.id', read_only=True)
    track_id = serializers.UUIDField(source='track.id', read_only=True)

    class Meta:
        model  = Like
        fields = ['id', 'user_id', 'track_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class DownloadSerializer(serializers.ModelSerializer):
    user_id  = serializers.UUIDField(source='user.id', read_only=True, allow_null=True)
    track_id = serializers.UUIDField(source='track.id', read_only=True)

    class Meta:
        model  = Download
        fields = ['id', 'user_id', 'track_id', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['id', 'created_at']


class PlaySerializer(serializers.ModelSerializer):
    user_id  = serializers.UUIDField(source='user.id', read_only=True, allow_null=True)
    track_id = serializers.UUIDField(source='track.id', read_only=True)

    class Meta:
        model  = Play
        fields = ['id', 'user_id', 'track_id', 'duration', 'completed', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['id', 'created_at']


class FollowSerializer(serializers.ModelSerializer):
    follower_id  = serializers.UUIDField(source='follower.id', read_only=True)
    following_id = serializers.UUIDField(source='following.id', read_only=True)

    class Meta:
        model  = Follow
        fields = ['id', 'follower_id', 'following_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class PlaylistTrackSerializer(serializers.ModelSerializer):
    track    = TrackSerializer(read_only=True)
    track_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model  = PlaylistTrack
        fields = ['id', 'track_id', 'track', 'order', 'added_at']
        read_only_fields = ['id', 'track', 'added_at']


class PlaylistSerializer(serializers.ModelSerializer):
    user_id      = serializers.UUIDField(source='user.id', read_only=True)
    tracks_count = serializers.SerializerMethodField()
    track_ids    = serializers.SerializerMethodField()

    class Meta:
        model  = Playlist
        fields = [
            'id', 'user_id', 'name', 'description', 'cover_url',
            'public', 'created_at', 'updated_at', 'tracks_count', 'track_ids',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tracks_count', 'track_ids']

    def get_tracks_count(self, obj):
        return obj.playlist_tracks.count()

    def get_track_ids(self, obj):
        return [str(item.track.id) for item in obj.playlist_tracks.all()]


class PlaylistDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    tracks  = PlaylistTrackSerializer(source='playlist_tracks', many=True, read_only=True)

    class Meta:
        model  = Playlist
        fields = [
            'id', 'user_id', 'name', 'description', 'cover_url',
            'public', 'created_at', 'updated_at', 'tracks',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tracks']


class CommentSerializer(serializers.ModelSerializer):
    user_id  = serializers.UUIDField(source='user.id', read_only=True)
    track_id = serializers.UUIDField(source='track.id', read_only=True)

    class Meta:
        model  = Comment
        fields = ['id', 'user_id', 'track_id', 'content', 'timestamp', 'likes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'likes', 'created_at', 'updated_at']


class UserStatsSerializer(serializers.Serializer):
    user_id           = serializers.UUIDField()
    total_tracks      = serializers.IntegerField()
    total_plays       = serializers.IntegerField()
    total_likes       = serializers.IntegerField()
    total_downloads   = serializers.IntegerField()
    total_followers   = serializers.IntegerField()
    total_following   = serializers.IntegerField()
    monthly_listeners = serializers.IntegerField()
    updated_at        = serializers.DateTimeField()


class TrackStatsSerializer(serializers.Serializer):
    track_id               = serializers.UUIDField()
    daily_plays            = serializers.DictField()
    total_unique_listeners = serializers.IntegerField()
    avg_listen_duration    = serializers.FloatField()
    completion_rate        = serializers.FloatField()
    updated_at             = serializers.DateTimeField()