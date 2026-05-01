import logging

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Sum, Avg, Max
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from datetime import timedelta

from .models import User, Track, Like, Download, Play, Follow, Album, Playlist, PlaylistTrack
from .serializers import (
    UserSerializer, PublicUserSerializer, UpdateUserSerializer, CreateUserSerializer,
    TrackSerializer, CreateTrackSerializer, UpdateTrackSerializer,
    LikeSerializer, DownloadSerializer, PlaySerializer, FollowSerializer,
    UserStatsSerializer, TrackStatsSerializer,
    AlbumSerializer, CreateAlbumSerializer, UpdateAlbumSerializer,
    PlaylistSerializer, PlaylistDetailSerializer, PlaylistTrackSerializer,
)

logger = logging.getLogger(__name__)


# ─── FileForge cleanup helpers ─────────────────────────────────────────────────

def _delete_fileforge_file(fileforge_id):
    """Silently delete a file from FileForge by its numeric ID."""
    if not fileforge_id:
        return
    from musewave.services.fileforge import delete_file
    try:
        delete_file(fileforge_id)
    except Exception as exc:
        logger.warning("Could not delete FileForge file %s: %s", fileforge_id, exc)


def _delete_track_files(track):
    """Delete a track's audio and cover files from FileForge."""
    _delete_fileforge_file(track.audio_fileforge_id)
    _delete_fileforge_file(track.cover_fileforge_id)


# ============================================================================
# USERS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user(request, user_id):
    """Public profile — email and other sensitive fields are excluded."""
    user = get_object_or_404(User, id=user_id)
    serializer = PublicUserSerializer(user, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_by_username(request, username):
    """Public profile lookup by username."""
    user = get_object_or_404(User, username=username)
    serializer = PublicUserSerializer(user, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_own_profile(request, user_id):
    """
    Full profile — only the authenticated owner may access their own record.
    GET /api/users/<id>/me
    """
    user = get_object_or_404(User, id=user_id)
    if request.user != user:
        return Response(
            {'error': 'You are not allowed to access this profile.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = UserSerializer(user, context={'request': request})
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_user(request, user_id):
    """
    Update own profile — only the authenticated owner may update their record.
    PATCH /api/users/<id>
    Accepts multipart/form-data with optional avatar_file / header_file files.
    """
    user = get_object_or_404(User, id=user_id)
    if request.user != user:
        return Response(
            {'error': 'You are not allowed to modify this profile.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = UpdateUserSerializer(
        user, data=request.data, partial=True, context={'request': request}
    )
    if serializer.is_valid():
        password = request.data.get('password')
        updated_user = serializer.save()
        if password:
            updated_user.set_password(password)
            updated_user.save(update_fields=['password'])
        return Response(UserSerializer(updated_user, context={'request': request}).data)

    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def users_create(request):
    """Public signup endpoint."""
    plain_password = request.data.get('password')
    serializer = CreateUserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Cache plain password for the email-verification flow (24 h)
        cache.set(f'user_password_{user.id}', plain_password, 86400)

        logger.info("New user created: %s (%s)", user.username, user.email)
        user_data = UserSerializer(user, context={'request': request}).data
        return Response({
            **user_data,
            'message': 'Account created successfully! Please check your email to verify your account.',
            'verification_required': True,
        }, status=status.HTTP_201_CREATED)

    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_list(request):
    """Protected — list users (paginated)."""
    limit  = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    users  = User.objects.all()[offset:offset + limit]
    serializer = UserSerializer(users, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def get_user_stats(request, user_id):
    user   = get_object_or_404(User, id=user_id)
    tracks = Track.objects.filter(user=user)

    total_plays     = tracks.aggregate(Sum('plays'))['plays__sum'] or 0
    total_likes     = tracks.aggregate(Sum('likes'))['likes__sum'] or 0
    total_downloads = tracks.aggregate(Sum('downloads'))['downloads__sum'] or 0
    total_followers = Follow.objects.filter(following=user).count()
    total_following = Follow.objects.filter(follower=user).count()

    thirty_days_ago  = timezone.now() - timedelta(days=30)
    track_ids        = tracks.values_list('id', flat=True)
    monthly_listeners = Play.objects.filter(
        track_id__in=track_ids,
        created_at__gte=thirty_days_ago,
    ).values('user').distinct().count()

    stats = {
        'user_id':           str(user.id),
        'total_tracks':      tracks.count(),
        'total_plays':       total_plays,
        'total_likes':       total_likes,
        'total_downloads':   total_downloads,
        'total_followers':   total_followers,
        'total_following':   total_following,
        'monthly_listeners': monthly_listeners,
        'updated_at':        timezone.now(),
    }
    return Response(UserStatsSerializer(stats).data)


@api_view(['GET'])
def get_artists(request):
    """Users who have at least one published track."""
    artist_ids = Track.objects.values_list('user', flat=True).distinct()
    artists    = User.objects.filter(id__in=artist_ids)
    return Response(PublicUserSerializer(artists, many=True, context={'request': request}).data)


# ============================================================================
# TRACKS
# ============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def tracks_list(request):
    tracks = Track.objects.all()

    user_id = request.GET.get('userId')
    if user_id:
        tracks = tracks.filter(user_id=user_id)

    genre = request.GET.get('genre')
    if genre:
        tracks = tracks.filter(genre__iexact=genre)

    mood = request.GET.get('mood')
    if mood:
        tracks = tracks.filter(mood__iexact=mood)

    tags = request.GET.get('tags')
    if tags:
        for tag in tags.split(','):
            tracks = tracks.filter(tags__contains=tag)

    published = request.GET.get('published')
    if published == 'true':
        tracks = tracks.filter(published=True)
    elif published == 'false':
        tracks = tracks.filter(published=False)

    sort_by    = request.GET.get('sortBy', 'created_at')
    sort_order = request.GET.get('sortOrder', 'desc')
    order_field = f'-{sort_by}' if sort_order == 'desc' else sort_by
    tracks = tracks.order_by(order_field)

    limit  = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))
    tracks = tracks[offset:offset + limit]

    return Response(TrackSerializer(tracks, many=True, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def tracks_create(request):
    serializer = CreateTrackSerializer(data=request.data)
    if serializer.is_valid():
        track = serializer.save()
        return Response(
            TrackSerializer(track, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def track_detail(request, track_id):
    track = get_object_or_404(Track, id=track_id)

    if request.method == 'GET':
        return Response(TrackSerializer(track, context={'request': request}).data)

    elif request.method == 'PATCH':
        serializer = UpdateTrackSerializer(track, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(TrackSerializer(track, context={'request': request}).data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        _delete_track_files(track)
        track.delete()
        return Response({'success': True})


@api_view(['DELETE'])
def delete_track_method(request, track_id):
    """Separate DELETE endpoint (kept for URL compatibility)."""
    track = get_object_or_404(Track, id=track_id)
    _delete_track_files(track)
    track.delete()
    return Response({'success': True})


@api_view(['GET', 'PATCH'])
def get_or_update_track(request, track_id):
    """Combined GET/PATCH kept for backward compatibility."""
    track = get_object_or_404(Track, id=track_id)

    if request.method == 'GET':
        return Response(TrackSerializer(track, context={'request': request}).data)

    serializer = UpdateTrackSerializer(track, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(TrackSerializer(track, context={'request': request}).data)
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_track_stats(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    plays = Play.objects.filter(track=track)

    daily_plays = {}
    for play in plays:
        date = play.created_at.date().isoformat()
        daily_plays[date] = daily_plays.get(date, 0) + 1

    unique_listeners = plays.values('user').distinct().count()
    avg_duration     = plays.aggregate(Avg('duration'))['duration__avg'] or 0
    total_plays      = plays.count()
    completed_plays  = plays.filter(completed=True).count()
    completion_rate  = (completed_plays / total_plays * 100) if total_plays > 0 else 0

    stats = {
        'track_id':               str(track.id),
        'daily_plays':            daily_plays,
        'total_unique_listeners': unique_listeners,
        'avg_listen_duration':    avg_duration,
        'completion_rate':        completion_rate,
        'updated_at':             timezone.now(),
    }
    return Response(TrackStatsSerializer(stats).data)


# ============================================================================
# LIKES
# ============================================================================

@api_view(['POST', 'DELETE'])
def like_track(request, track_id):
    if request.method == 'POST':
        user_id = request.data.get('userId')
        if not user_id:
            return Response({'error': 'userId is required'}, status=status.HTTP_400_BAD_REQUEST)
        user  = get_object_or_404(User, id=user_id)
        track = get_object_or_404(Track, id=track_id)
        like, created = Like.objects.get_or_create(user=user, track=track)
        if created:
            track.likes += 1
            track.save()
        return Response(
            LikeSerializer(like).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    user_id = request.data.get('userId')
    if not user_id:
        return Response({'error': 'userId is required'}, status=status.HTTP_400_BAD_REQUEST)
    user  = get_object_or_404(User, id=user_id)
    track = get_object_or_404(Track, id=track_id)
    try:
        like = Like.objects.get(user=user, track=track)
        like.delete()
        track.likes = max(0, track.likes - 1)
        track.save()
        return Response({'success': True})
    except Like.DoesNotExist:
        return Response({'error': 'Like not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def check_like(request, track_id, user_id):
    has_liked = Like.objects.filter(user_id=user_id, track_id=track_id).exists()
    return Response({'hasLiked': has_liked})


@api_view(['GET'])
def get_user_likes(request, user_id):
    likes = Like.objects.filter(user_id=user_id)
    return Response(LikeSerializer(likes, many=True).data)


# ============================================================================
# DOWNLOADS
# ============================================================================

@api_view(['POST'])
def create_download(request, track_id):
    track   = get_object_or_404(Track, id=track_id)
    user_id = request.data.get('userId')
    user    = get_object_or_404(User, id=user_id) if user_id else None

    download = Download.objects.create(
        user=user, track=track,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
    )
    track.downloads += 1
    track.save()
    return Response(DownloadSerializer(download).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_track_downloads(request, track_id):
    downloads = Download.objects.filter(track_id=track_id)
    return Response(DownloadSerializer(downloads, many=True).data)


# ============================================================================
# PLAYS
# ============================================================================

@api_view(['POST'])
def create_play(request, track_id):
    track   = get_object_or_404(Track, id=track_id)
    user_id = request.data.get('userId')
    user    = get_object_or_404(User, id=user_id) if user_id else None

    play = Play.objects.create(
        user=user, track=track,
        duration=request.data.get('duration', 0),
        completed=request.data.get('completed', False),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
    )
    track.plays += 1
    track.save()
    return Response(PlaySerializer(play).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_track_plays(request, track_id):
    plays = Play.objects.filter(track_id=track_id)
    return Response(PlaySerializer(plays, many=True).data)


@api_view(['GET'])
def get_user_plays(request, user_id):
    plays = Play.objects.filter(user_id=user_id)
    return Response(PlaySerializer(plays, many=True).data)


# ============================================================================
# FOLLOWS
# ============================================================================

@api_view(['POST', 'DELETE'])
def follow_user(request, user_id):
    if request.method == 'POST':
        follower_id = request.data.get('followerId')
        if not follower_id:
            return Response({'error': 'followerId is required'}, status=status.HTTP_400_BAD_REQUEST)
        follower  = get_object_or_404(User, id=follower_id)
        following = get_object_or_404(User, id=user_id)
        follow, created = Follow.objects.get_or_create(follower=follower, following=following)
        return Response(
            FollowSerializer(follow).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    follower_id = request.data.get('followerId')
    if not follower_id:
        return Response({'error': 'followerId is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        follow = Follow.objects.get(follower_id=follower_id, following_id=user_id)
        follow.delete()
        return Response({'success': True})
    except Follow.DoesNotExist:
        return Response({'error': 'Follow not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def check_follow(request, user_id, follower_id):
    is_following = Follow.objects.filter(follower_id=follower_id, following_id=user_id).exists()
    return Response({'isFollowing': is_following})


@api_view(['GET'])
def get_followers(request, user_id):
    follows = Follow.objects.filter(following_id=user_id)
    return Response(FollowSerializer(follows, many=True).data)


@api_view(['GET'])
def get_following(request, user_id):
    follows = Follow.objects.filter(follower_id=user_id)
    return Response(FollowSerializer(follows, many=True).data)


# ============================================================================
# ALBUMS
# ============================================================================

@api_view(['GET'])
def get_user_albums(request, user_id):
    albums = Album.objects.filter(user_id=user_id)
    return Response(AlbumSerializer(albums, many=True, context={'request': request}).data)


@api_view(['GET'])
def get_album(request, album_id):
    album  = get_object_or_404(Album, id=album_id)
    tracks = Track.objects.filter(album=album)
    data   = AlbumSerializer(album, context={'request': request}).data
    data['tracks'] = TrackSerializer(tracks, many=True, context={'request': request}).data
    return Response(data)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def create_album(request):
    serializer = CreateAlbumSerializer(data=request.data)
    if serializer.is_valid():
        album = serializer.save()
        return Response(
            AlbumSerializer(album, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_album(request, album_id):
    album      = get_object_or_404(Album, id=album_id)
    serializer = UpdateAlbumSerializer(album, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(AlbumSerializer(album, context={'request': request}).data)
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_album(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    _delete_fileforge_file(album.cover_fileforge_id)
    Track.objects.filter(album=album).update(album=None)
    album.delete()
    return Response({'success': True})


# ============================================================================
# SEARCH
# ============================================================================

@api_view(['GET'])
def search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return Response({'error': "Query parameter 'q' is required"}, status=status.HTTP_400_BAD_REQUEST)

    search_type = request.GET.get('type', 'all')
    limit       = int(request.GET.get('limit', 20))
    results     = {'tracks': [], 'users': []}

    if search_type in ['tracks', 'all']:
        tracks = Track.objects.filter(
            Q(title__icontains=query) | Q(artist__icontains=query) |
            Q(genre__icontains=query) | Q(mood__icontains=query) |
            Q(tags__icontains=query),
            published=True,
        )[:limit]
        results['tracks'] = TrackSerializer(tracks, many=True).data

    if search_type in ['users', 'all']:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(display_name__icontains=query) |
            Q(bio__icontains=query),
        )[:limit]
        results['users'] = PublicUserSerializer(users, many=True).data

    return Response(results)


@api_view(['POST'])
def rebuild_search_index(request):
    return Response({'success': True})


# ============================================================================
# AUDIO STREAMING AND DOWNLOAD
# ============================================================================

@api_view(['GET'])
def stream_track(request, track_id):
    return Response(
        {'detail': 'Use /api/tracks/{id}/stream/ via TrackStreamView.'},
        status=status.HTTP_501_NOT_IMPLEMENTED,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_track(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    if not track.audio_url:
        return Response({'error': 'Audio file not found'}, status=status.HTTP_404_NOT_FOUND)

    Download.objects.create(
        user=request.user, track=track,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    track.downloads += 1
    track.save(update_fields=['downloads'])

    return Response({'audio_url': track.audio_url})


@api_view(['GET'])
def get_track_stream_url(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    if not track.audio_url:
        return Response({'error': 'Audio file not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'id':         str(track.id),
        'title':      track.title,
        'artist':     track.artist,
        'stream_url': track.audio_url,
        'duration':   track.audio_duration,
        'format':     track.audio_format or 'mp3',
    })


# ============================================================================
# PLAYLISTS
# ============================================================================

@api_view(['GET', 'POST'])
def playlists_list_or_create(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'GET':
        playlists  = Playlist.objects.filter(user=request.user).prefetch_related('playlist_tracks__track')
        serializer = PlaylistSerializer(playlists, many=True, context={'request': request})
        return Response(serializer.data)

    serializer = PlaylistSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH', 'DELETE'])
def playlist_detail(request, playlist_id):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)

    if request.method == 'GET':
        return Response(PlaylistDetailSerializer(playlist, context={'request': request}).data)

    elif request.method == 'PATCH':
        serializer = PlaylistSerializer(playlist, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    playlist.delete()
    return Response({'success': True})


@api_view(['POST'])
def add_track_to_playlist(request, playlist_id):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    track_id = request.data.get('track_id')
    if not track_id:
        return Response({'error': 'track_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    track = get_object_or_404(Track, id=track_id)
    if PlaylistTrack.objects.filter(playlist=playlist, track=track).exists():
        return Response({'error': 'Track already exists in playlist'}, status=status.HTTP_400_BAD_REQUEST)

    max_order  = PlaylistTrack.objects.filter(playlist=playlist).aggregate(Max('order'))['order__max']
    next_order = 0 if max_order is None else max_order + 1
    pt         = PlaylistTrack.objects.create(playlist=playlist, track=track, order=next_order)
    return Response(PlaylistTrackSerializer(pt, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def remove_track_from_playlist(request, playlist_id):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    track_id = request.data.get('track_id')
    if not track_id:
        return Response({'error': 'track_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pt = PlaylistTrack.objects.get(playlist=playlist, track_id=track_id)
    except PlaylistTrack.DoesNotExist:
        return Response({'error': 'Track not found in playlist'}, status=status.HTTP_404_NOT_FOUND)

    pt.delete()
    return Response({'success': True})


@api_view(['POST'])
def reorder_playlist_tracks(request, playlist_id):
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    payload  = request.data

    if not isinstance(payload, list):
        return Response({'error': 'Payload must be a list of {"id", "order"} objects'}, status=status.HTTP_400_BAD_REQUEST)

    ids = [item.get('id') for item in payload if isinstance(item, dict)]
    if len(ids) != len(payload) or None in ids:
        return Response({'error': 'Each item must contain an "id" field'}, status=status.HTTP_400_BAD_REQUEST)

    order_values = [item.get('order') for item in payload]
    if any(not isinstance(o, int) for o in order_values):
        return Response({'error': 'Each "order" must be an integer'}, status=status.HTTP_400_BAD_REQUEST)

    if len(order_values) != len(set(order_values)):
        return Response({'error': 'Duplicate order values are not allowed'}, status=status.HTTP_400_BAD_REQUEST)

    playlist_tracks = PlaylistTrack.objects.filter(playlist=playlist, id__in=ids)
    if playlist_tracks.count() != len(ids):
        return Response({'error': 'One or more playlist track entries are invalid'}, status=status.HTTP_400_BAD_REQUEST)

    track_map = {str(pt.id): pt for pt in playlist_tracks}
    updates   = []
    for item in payload:
        pt = track_map.get(str(item['id']))
        if not pt:
            return Response({'error': f'Invalid playlist track id: {item["id"]}'}, status=status.HTTP_400_BAD_REQUEST)
        pt.order = item['order']
        updates.append(pt)

    PlaylistTrack.objects.bulk_update(updates, ['order'])
    return Response({'success': True})