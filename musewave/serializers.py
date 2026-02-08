from rest_framework import serializers
from .models import User, Track, Like, Download, Play, Follow, Playlist, Comment, Album


class UserSerializer(serializers.ModelSerializer):
    social_links = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'display_name', 'bio', 
            'avatar_url', 'header_url', 'location', 'website',
            'social_links', 'verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'verified']
    
    def get_social_links(self, obj):
        return {
            'twitter': obj.twitter,
            'instagram': obj.instagram,
            'spotify': obj.spotify,
            'soundcloud': obj.soundcloud,
        }


class CreateUserSerializer(serializers.ModelSerializer):
    twitter = serializers.CharField(required=False, allow_blank=True)
    instagram = serializers.CharField(required=False, allow_blank=True)
    spotify = serializers.CharField(required=False, allow_blank=True)
    soundcloud = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'display_name', 'bio',
            'avatar_url', 'header_url', 'location', 'website',
            'twitter', 'instagram', 'spotify', 'soundcloud'
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


class AlbumSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    track_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Album
        fields = [
            'id', 'user_id', 'title', 'artist', 'description',
            'cover_url', 'cover_gradient', 'release_date', 'genre',
            'published', 'created_at', 'updated_at', 'track_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_track_count(self, obj):
        return obj.tracks.count()


class CreateAlbumSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    track_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Album
        fields = [
            'user_id', 'title', 'artist', 'description',
            'cover_url', 'cover_gradient', 'release_date', 'genre',
            'published', 'track_ids'
        ]
    
    def create(self, validated_data):
        track_ids = validated_data.pop('track_ids', [])
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        
        album = Album.objects.create(user=user, **validated_data)
        
        # Associate tracks with album
        if track_ids:
            Track.objects.filter(id__in=track_ids).update(album=album)
        
        return album


class TrackSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    album_id = serializers.UUIDField(source='album.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Track
        fields = [
            'id', 'user_id', 'album_id', 'title', 'artist', 'artist_slug', 'description',
            'genre', 'mood', 'tags', 'audio_url', 'audio_file_size',
            'audio_duration', 'audio_format', 'cover_url', 'cover_gradient',
            'waveform_data', 'bpm', 'key', 'plays', 'likes', 'downloads',
            'shares', 'published', 'published_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'plays', 'likes', 'downloads', 'shares',
            'published_at', 'created_at', 'updated_at'
        ]


class CreateTrackSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Track
        fields = [
            'user_id', 'title', 'artist', 'artist_slug', 'description',
            'genre', 'mood', 'tags', 'audio_url', 'audio_file_size',
            'audio_duration', 'audio_format', 'cover_url', 'cover_gradient',
            'waveform_data', 'bpm', 'key', 'published'
        ]
    
    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        track = Track.objects.create(user=user, **validated_data)
        return track


class UpdateTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = [
            'title', 'artist', 'artist_slug', 'description', 'genre', 'mood',
            'tags', 'audio_url', 'audio_file_size', 'audio_duration',
            'audio_format', 'cover_url', 'cover_gradient', 'waveform_data',
            'bpm', 'key', 'published'
        ]
    
    def update(self, instance, validated_data):
        # Handle published_at timestamp
        if 'published' in validated_data and validated_data['published'] and not instance.published:
            from django.utils import timezone
            instance.published_at = timezone.now()
        
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


class PlaylistSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    track_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = Playlist
        fields = ['id', 'user_id', 'name', 'description', 'cover_url', 'track_ids', 'public', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_track_ids(self, obj):
        return [str(track.id) for track in obj.tracks.all()]


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
