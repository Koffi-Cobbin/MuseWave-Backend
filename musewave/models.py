from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.utils import timezone
import uuid


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Store hashed passwords
    display_name = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    header_url = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Social links stored as JSON
    twitter = models.CharField(max_length=100, blank=True, null=True)
    instagram = models.CharField(max_length=100, blank=True, null=True)
    spotify = models.CharField(max_length=100, blank=True, null=True)
    soundcloud = models.CharField(max_length=100, blank=True, null=True)
    
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return self.username


class Album(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='albums')
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    description = models.TextField(max_length=2000, blank=True, null=True)
    cover_url = models.URLField(blank=True, null=True)
    cover_gradient = models.CharField(max_length=255, blank=True, null=True)
    release_date = models.DateTimeField()
    genre = models.CharField(max_length=50)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'albums'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.artist} - {self.title}"


class Track(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tracks')
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, blank=True, related_name='tracks')
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    artist_slug = models.SlugField(max_length=200)
    description = models.TextField(max_length=2000, blank=True, null=True)
    genre = models.CharField(max_length=50)
    mood = models.CharField(max_length=50, blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    
    # File information
    audio_url = models.URLField()
    audio_file_size = models.BigIntegerField()  # bytes
    audio_duration = models.FloatField()  # seconds
    audio_format = models.CharField(max_length=20)  # mp3, wav, etc.
    
    cover_url = models.URLField(blank=True, null=True)
    cover_gradient = models.CharField(max_length=255, blank=True, null=True)
    waveform_data = models.TextField(blank=True, null=True)  # JSON string
    
    # Metadata
    bpm = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1)])
    key = models.CharField(max_length=10, blank=True, null=True)  # Musical key
    
    # Stats
    plays = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    
    # Status
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tracks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'published']),
            models.Index(fields=['genre']),
            models.Index(fields=['-plays']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.artist} - {self.title}"


class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='track_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'likes'
        unique_together = ['user', 'track']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} likes {self.track.title}"


class Download(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='downloads')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='track_downloads')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'downloads'
        ordering = ['-created_at']

    def __str__(self):
        return f"Download of {self.track.title}"


class Play(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='plays')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='track_plays')
    duration = models.FloatField(default=0)  # How long they listened in seconds
    completed = models.BooleanField(default=False)  # Did they listen to >80%?
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'plays'
        ordering = ['-created_at']

    def __str__(self):
        return f"Play of {self.track.title}"


class Follow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'follows'
        unique_together = ['follower', 'following']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Playlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True, null=True)
    cover_url = models.URLField(blank=True, null=True)
    tracks = models.ManyToManyField(Track, related_name='in_playlists', blank=True)
    public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'playlists'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='comments')
    content = models.CharField(max_length=500)
    timestamp = models.FloatField(blank=True, null=True)  # Position in track (seconds)
    likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.track.title}"
