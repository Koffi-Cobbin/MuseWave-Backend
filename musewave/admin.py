from django.contrib import admin
from .models import User, Track, Like, Download, Play, Follow, Playlist, Comment, Album


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'display_name', 'verified', 'created_at']
    list_filter = ['verified', 'created_at']
    search_fields = ['username', 'email', 'display_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'user', 'genre', 'published', 'created_at']
    list_filter = ['published', 'genre', 'created_at']
    search_fields = ['title', 'artist', 'genre']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'album', 'genre', 'plays', 'likes', 'published', 'created_at']
    list_filter = ['published', 'genre', 'created_at']
    search_fields = ['title', 'artist', 'genre']
    readonly_fields = ['id', 'plays', 'likes', 'downloads', 'shares', 'created_at', 'updated_at']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'track', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'track__title']


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ['track', 'user', 'ip_address', 'created_at']
    list_filter = ['created_at']
    search_fields = ['track__title', 'user__username']


@admin.register(Play)
class PlayAdmin(admin.ModelAdmin):
    list_display = ['track', 'user', 'duration', 'completed', 'created_at']
    list_filter = ['completed', 'created_at']
    search_fields = ['track__title', 'user__username']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'public', 'created_at']
    list_filter = ['public', 'created_at']
    search_fields = ['name', 'user__username']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'track', 'content', 'timestamp', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'track__title', 'content']
