from rest_framework import serializers
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .models import User, Track, Like, Download, Play, Follow, Playlist, PlaylistTrack, Comment, Album


class UserSerializer(serializers.ModelSerializer):
    social_links = serializers.SerializerMethodField()

    # Read-only computed URL fields returned to the frontend
    avatar_url = serializers.SerializerMethodField()
    header_url = serializers.SerializerMethodField()

    # Write-only fields that accept uploaded image files
    avatar_file = serializers.ImageField(
        write_only=True, required=False, allow_null=True
    )
    header_file = serializers.ImageField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name', 'bio',
            'avatar_url', 'header_url',
            'avatar_file', 'header_file',
            'location', 'website',
            'social_links', 'verified', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'verified']

    def get_avatar_url(self, obj):
        if obj.avatar_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar_file.url)
            return obj.avatar_file.url
        return None

    def get_header_url(self, obj):
        if obj.header_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.header_file.url)
            return obj.header_file.url
        return None

    def get_social_links(self, obj):
        return {
            'twitter': obj.twitter,
            'instagram': obj.instagram,
            'spotify': obj.spotify,
            'soundcloud': obj.soundcloud,
        }

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CreateUserSerializer(serializers.ModelSerializer):
    twitter = serializers.CharField(required=False, allow_blank=True)
    instagram = serializers.CharField(required=False, allow_blank=True)
    spotify = serializers.CharField(required=False, allow_blank=True)
    soundcloud = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'display_name', 'bio',
            'avatar_file', 'header_file', 'location', 'website',
            'twitter', 'instagram', 'spotify', 'soundcloud',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'username': {'min_length': 3, 'max_length': 30},
            'bio': {'max_length': 500},
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
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.verified = False
        user.save()

        user._plain_password = password

        self.send_verification_email(user)

        return user

    def send_verification_email(self, user):
        try:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # ----------------------------------------------------------------
            # Link goes to the FRONTEND /verify-email page.
            # The frontend reads uid + token from the URL and calls:
            #   GET /api/users/verify-email/<uid>/<token>/
            # ----------------------------------------------------------------
            verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"

            subject = 'Verify Your MuseWave Account'

            message = f"""
Hello {user.display_name or user.username}!

Thank you for registering with MuseWave!

To complete your registration and activate your account, please verify your email address by clicking the link below:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERIFY YOUR EMAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{verification_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This link will expire in 24 hours.

After verification, you will receive a welcome email with your login credentials.

If you didn't create this account, please ignore this email.

Best regards,
The MuseWave Team

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated message. Please do not reply to this email.
            """

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            print(f"✅ Verification email sent to {user.email}")
            print(f"🔗 Verification URL: {verification_url}")

        except Exception as e:
            print(f"❌ Failed to send verification email to {user.email}: {str(e)}")


class AlbumSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    track_count = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = [
            'id', 'user_id', 'title', 'artist', 'description',
            'cover_url', 'cover_gradient', 'release_date', 'genre',
            'published', 'created_at', 'updated_at', 'track_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_track_count(self, obj):
        return obj.tracks.count()

    def get_cover_url(self, obj):
        if obj.cover_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_file.url)
            return obj.cover_file.url
        return None


class CreateAlbumSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    cover_file = serializers.ImageField(write_only=True, required=False, allow_null=True)
    track_ids = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Album
        fields = [
            'user_id', 'title', 'artist', 'description',
            'cover_file', 'cover_gradient', 'release_date', 'genre',
            'published', 'track_ids',
        ]

    def create(self, validated_data):
        track_ids_raw = validated_data.pop('track_ids', [])
        if isinstance(track_ids_raw, str):
            import json
            try:
                track_ids = json.loads(track_ids_raw)
            except json.JSONDecodeError:
                track_ids = []
        else:
            track_ids = track_ids_raw

        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)

        album = Album.objects.create(user=user, **validated_data)

        if track_ids:
            Track.objects.filter(id__in=track_ids).update(album=album)

        return album


class TrackSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    album_id = serializers.UUIDField(source='album.id', read_only=True, allow_null=True)
    audio_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()

    class Meta:
        model = Track
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
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None

    def get_cover_url(self, obj):
        if obj.cover_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_file.url)
            return obj.cover_file.url
        return None


class CreateTrackSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    audio_file = serializers.FileField(write_only=True)
    cover_file = serializers.ImageField(write_only=True, required=False, allow_null=True)
    tags = serializers.JSONField(required=False)

    class Meta:
        model = Track
        fields = [
            'user_id', 'title', 'artist', 'artist_slug', 'description',
            'genre', 'mood', 'tags', 'audio_file', 'audio_file_size',
            'audio_duration', 'audio_format', 'cover_file', 'cover_gradient',
            'waveform_data', 'bpm', 'key', 'published',
        ]

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)

        if 'tags' in validated_data and isinstance(validated_data['tags'], str):
            import json
            try:
                validated_data['tags'] = json.loads(validated_data['tags'])
            except json.JSONDecodeError:
                validated_data['tags'] = []

        if validated_data.get('published', False):
            from django.utils import timezone
            validated_data['published_at'] = timezone.now()

        track = Track.objects.create(user=user, **validated_data)
        return track


class UpdateTrackSerializer(serializers.ModelSerializer):
    audio_file = serializers.FileField(required=False)
    cover_file = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Track
        fields = [
            'title', 'artist', 'artist_slug', 'description', 'genre', 'mood',
            'tags', 'audio_file', 'audio_file_size', 'audio_duration',
            'audio_format', 'cover_file', 'cover_gradient', 'waveform_data',
            'bpm', 'key', 'published',
        ]

    def update(self, instance, validated_data):
        if 'published' in validated_data and validated_data['published'] and not instance.published:
            from django.utils import timezone
            instance.published_at = timezone.now()

        if 'tags' in validated_data and isinstance(validated_data['tags'], str):
            import json
            try:
                validated_data['tags'] = json.loads(validated_data['tags'])
            except json.JSONDecodeError:
                pass

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class LikeSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    track_id = serializers.UUIDField(source='track.id', read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user_id', 'track_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class DownloadSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True, allow_null=True)
    track_id = serializers.UUIDField(source='track.id', read_only=True)

    class Meta:
        model = Download
        fields = ['id', 'user_id', 'track_id', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['id', 'created_at']


class PlaySerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True, allow_null=True)
    track_id = serializers.UUIDField(source='track.id', read_only=True)

    class Meta:
        model = Play
        fields = ['id', 'user_id', 'track_id', 'duration', 'completed', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['id', 'created_at']


class FollowSerializer(serializers.ModelSerializer):
    follower_id = serializers.UUIDField(source='follower.id', read_only=True)
    following_id = serializers.UUIDField(source='following.id', read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower_id', 'following_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class PlaylistTrackSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    track_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = PlaylistTrack
        fields = ['id', 'track_id', 'track', 'order', 'added_at']
        read_only_fields = ['id', 'track', 'added_at']


class PlaylistSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    tracks_count = serializers.SerializerMethodField()
    track_ids = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
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
    tracks = PlaylistTrackSerializer(source='playlist_tracks', many=True, read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id', 'user_id', 'name', 'description', 'cover_url',
            'public', 'created_at', 'updated_at', 'tracks',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tracks']


class CommentSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    track_id = serializers.UUIDField(source='track.id', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user_id', 'track_id', 'content', 'timestamp', 'likes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'likes', 'created_at', 'updated_at']


class UserStatsSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    total_tracks = serializers.IntegerField()
    total_plays = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_downloads = serializers.IntegerField()
    total_followers = serializers.IntegerField()
    total_following = serializers.IntegerField()
    monthly_listeners = serializers.IntegerField()
    updated_at = serializers.DateTimeField()


class TrackStatsSerializer(serializers.Serializer):
    track_id = serializers.UUIDField()
    daily_plays = serializers.DictField()
    total_unique_listeners = serializers.IntegerField()
    avg_listen_duration = serializers.FloatField()
    completion_rate = serializers.FloatField()
    updated_at = serializers.DateTimeField()