from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import timedelta

from .models import User, Track, Like, Download, Play, Follow, Album
from .serializers import (
    UserSerializer, CreateUserSerializer, TrackSerializer,
    CreateTrackSerializer, UpdateTrackSerializer, LikeSerializer,
    DownloadSerializer, PlaySerializer, FollowSerializer,
    UserStatsSerializer, TrackStatsSerializer, AlbumSerializer, CreateAlbumSerializer
)


# ============================================================================
# USERS
# ============================================================================

@api_view(['GET'])
def get_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['GET'])
def get_user_by_username(request, username):
    user = get_object_or_404(User, username=username)
    serializer = UserSerializer(user)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
def users_list_or_create(request):
    """Handle both listing users and creating new users"""
    if request.method == 'GET':
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        
        users = User.objects.all()[offset:offset + limit]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CreateUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user_data = UserSerializer(user).data
            return Response(user_data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'GET'])
def get_or_update_track(request, track_id):
    """Combined endpoint for GET and PATCH on tracks"""
    track = get_object_or_404(Track, id=track_id)
    
    if request.method == 'GET':
        serializer = TrackSerializer(track)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = UpdateTrackSerializer(track, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            track_data = TrackSerializer(track).data
            return Response(track_data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_track_method(request, track_id):
    """Separate DELETE endpoint"""
    track = get_object_or_404(Track, id=track_id)
    track.delete()
    return Response({'success': True})


@api_view(['POST', 'DELETE'])
def like_track(request, track_id):
    """Combined endpoint for creating and deleting likes"""
    if request.method == 'POST':
        user_id = request.data.get('userId')
        if not user_id:
            return Response({'error': 'userId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, id=user_id)
        track = get_object_or_404(Track, id=track_id)
        
        # Check if already liked
        like, created = Like.objects.get_or_create(user=user, track=track)
        
        if created:
            # Increment track likes
            track.likes += 1
            track.save()
        
        serializer = LikeSerializer(like)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        user_id = request.data.get('userId')
        if not user_id:
            return Response({'error': 'userId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, id=user_id)
        track = get_object_or_404(Track, id=track_id)
        
        try:
            like = Like.objects.get(user=user, track=track)
            like.delete()
            
            # Decrement track likes
            track.likes = max(0, track.likes - 1)
            track.save()
            
            return Response({'success': True})
        except Like.DoesNotExist:
            return Response({'error': 'Like not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST', 'DELETE'])
def follow_user(request, user_id):
    """Combined endpoint for following and unfollowing"""
    if request.method == 'POST':
        follower_id = request.data.get('followerId')
        if not follower_id:
            return Response({'error': 'followerId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        follower = get_object_or_404(User, id=follower_id)
        following = get_object_or_404(User, id=user_id)
        
        # Check if already following
        follow, created = Follow.objects.get_or_create(follower=follower, following=following)
        
        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        follower_id = request.data.get('followerId')
        if not follower_id:
            return Response({'error': 'followerId is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            follow = Follow.objects.get(follower_id=follower_id, following_id=user_id)
            follow.delete()
            return Response({'success': True})
        except Follow.DoesNotExist:
            return Response({'error': 'Follow not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH', 'GET'])
def get_or_update_user(request, user_id):
    """Combined endpoint for GET and PATCH on users"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_user_stats(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Get user's tracks
    tracks = Track.objects.filter(user=user)
    
    # Calculate stats
    total_plays = tracks.aggregate(Sum('plays'))['plays__sum'] or 0
    total_likes = tracks.aggregate(Sum('likes'))['likes__sum'] or 0
    total_downloads = tracks.aggregate(Sum('downloads'))['downloads__sum'] or 0
    total_followers = Follow.objects.filter(following=user).count()
    total_following = Follow.objects.filter(follower=user).count()
    
    # Monthly listeners (unique users in last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    track_ids = tracks.values_list('id', flat=True)
    monthly_listeners = Play.objects.filter(
        track_id__in=track_ids,
        created_at__gte=thirty_days_ago
    ).values('user').distinct().count()
    
    stats = {
        'user_id': str(user.id),
        'total_tracks': tracks.count(),
        'total_plays': total_plays,
        'total_likes': total_likes,
        'total_downloads': total_downloads,
        'total_followers': total_followers,
        'total_following': total_following,
        'monthly_listeners': monthly_listeners,
        'updated_at': timezone.now()
    }
    
    serializer = UserStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
def get_artists(request):
    """Get users who have published tracks"""
    artist_ids = Track.objects.values_list('user', flat=True).distinct()
    artists = User.objects.filter(id__in=artist_ids)
    serializer = UserSerializer(artists, many=True)
    return Response(serializer.data)


# ============================================================================
# TRACKS
# ============================================================================

@api_view(['GET', 'POST'])
def tracks_list_or_create(request):
    """Handle both listing tracks and creating new tracks"""
    if request.method == 'GET':
        tracks = Track.objects.all()
        
        # Apply filters
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
            tag_list = tags.split(',')
            for tag in tag_list:
                tracks = tracks.filter(tags__contains=tag)
        
        published = request.GET.get('published')
        if published == 'true':
            tracks = tracks.filter(published=True)
        elif published == 'false':
            tracks = tracks.filter(published=False)
        
        # Sorting
        sort_by = request.GET.get('sortBy', 'created_at')
        sort_order = request.GET.get('sortOrder', 'desc')
        
        order_field = f'-{sort_by}' if sort_order == 'desc' else sort_by
        tracks = tracks.order_by(order_field)
        
        # Pagination
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        tracks = tracks[offset:offset + limit]
        
        serializer = TrackSerializer(tracks, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CreateTrackSerializer(data=request.data)
        if serializer.is_valid():
            track = serializer.save()
            track_data = TrackSerializer(track).data
            return Response(track_data, status=status.HTTP_201_CREATED)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET', 'PATCH', 'DELETE'])
def track_detail(request, track_id):
    """Combined endpoint for all track operations"""
    if request.method == 'GET':
        track = get_object_or_404(Track, id=track_id)
        serializer = TrackSerializer(track)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        track = get_object_or_404(Track, id=track_id)
        serializer = UpdateTrackSerializer(track, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            track_data = TrackSerializer(track).data
            return Response(track_data)
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        track = get_object_or_404(Track, id=track_id)
        track.delete()
        return Response({'success': True})


@api_view(['GET'])
def get_track_stats(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    plays = Play.objects.filter(track=track)
    
    # Daily plays
    daily_plays = {}
    for play in plays:
        date = play.created_at.date().isoformat()
        daily_plays[date] = daily_plays.get(date, 0) + 1
    
    # Unique listeners
    unique_listeners = plays.values('user').distinct().count()
    
    # Average listen duration
    avg_duration = plays.aggregate(Avg('duration'))['duration__avg'] or 0
    
    # Completion rate
    total_plays = plays.count()
    completed_plays = plays.filter(completed=True).count()
    completion_rate = (completed_plays / total_plays * 100) if total_plays > 0 else 0
    
    stats = {
        'track_id': str(track.id),
        'daily_plays': daily_plays,
        'total_unique_listeners': unique_listeners,
        'avg_listen_duration': avg_duration,
        'completion_rate': completion_rate,
        'updated_at': timezone.now()
    }
    
    serializer = TrackStatsSerializer(stats)
    return Response(serializer.data)


# ============================================================================
# LIKES
# ============================================================================

# ============================================================================
# DOWNLOADS
# ============================================================================

@api_view(['POST'])
def create_download(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    user_id = request.data.get('userId')
    
    user = None
    if user_id:
        user = get_object_or_404(User, id=user_id)
    
    download = Download.objects.create(
        user=user,
        track=track,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    # Increment track downloads
    track.downloads += 1
    track.save()
    
    serializer = DownloadSerializer(download)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_track_downloads(request, track_id):
    downloads = Download.objects.filter(track_id=track_id)
    serializer = DownloadSerializer(downloads, many=True)
    return Response(serializer.data)


# ============================================================================
# PLAYS
# ============================================================================

@api_view(['POST'])
def create_play(request, track_id):
    track = get_object_or_404(Track, id=track_id)
    user_id = request.data.get('userId')
    
    user = None
    if user_id:
        user = get_object_or_404(User, id=user_id)
    
    play = Play.objects.create(
        user=user,
        track=track,
        duration=request.data.get('duration', 0),
        completed=request.data.get('completed', False),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    # Increment track plays
    track.plays += 1
    track.save()
    
    serializer = PlaySerializer(play)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_track_plays(request, track_id):
    plays = Play.objects.filter(track_id=track_id)
    serializer = PlaySerializer(plays, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_user_plays(request, user_id):
    plays = Play.objects.filter(user_id=user_id)
    serializer = PlaySerializer(plays, many=True)
    return Response(serializer.data)


# Keep the check like and get user likes functions
@api_view(['GET'])
def check_like(request, track_id, user_id):
    has_liked = Like.objects.filter(user_id=user_id, track_id=track_id).exists()
    return Response({'hasLiked': has_liked})


@api_view(['GET'])
def get_user_likes(request, user_id):
    likes = Like.objects.filter(user_id=user_id)
    serializer = LikeSerializer(likes, many=True)
    return Response(serializer.data)


# Keep the check follow and get followers/following functions
@api_view(['GET'])
def check_follow(request, user_id, follower_id):
    is_following = Follow.objects.filter(follower_id=follower_id, following_id=user_id).exists()
    return Response({'isFollowing': is_following})


@api_view(['GET'])
def get_followers(request, user_id):
    follows = Follow.objects.filter(following_id=user_id)
    serializer = FollowSerializer(follows, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_following(request, user_id):
    follows = Follow.objects.filter(follower_id=user_id)
    serializer = FollowSerializer(follows, many=True)
    return Response(serializer.data)


# ============================================================================
# ALBUMS
# ============================================================================

@api_view(['GET'])
def get_user_albums(request, user_id):
    """Get all albums for a user"""
    albums = Album.objects.filter(user_id=user_id)
    serializer = AlbumSerializer(albums, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_album(request, album_id):
    """Get album by ID with tracks"""
    album = get_object_or_404(Album, id=album_id)
    tracks = Track.objects.filter(album=album)
    
    album_data = AlbumSerializer(album).data
    album_data['tracks'] = TrackSerializer(tracks, many=True).data
    
    return Response(album_data)


@api_view(['POST'])
def create_album(request):
    """Create a new album"""
    serializer = CreateAlbumSerializer(data=request.data)
    if serializer.is_valid():
        album = serializer.save()
        album_data = AlbumSerializer(album).data
        return Response(album_data, status=status.HTTP_201_CREATED)
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def update_album(request, album_id):
    """Update an album"""
    album = get_object_or_404(Album, id=album_id)
    serializer = AlbumSerializer(album, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_album(request, album_id):
    """Delete an album"""
    album = get_object_or_404(Album, id=album_id)
    
    # Remove album association from tracks (don't delete the tracks)
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
    limit = int(request.GET.get('limit', 20))
    
    results = {
        'tracks': [],
        'users': []
    }
    
    # Search tracks
    if search_type in ['tracks', 'all']:
        tracks = Track.objects.filter(
            Q(title__icontains=query) |
            Q(artist__icontains=query) |
            Q(genre__icontains=query) |
            Q(mood__icontains=query) |
            Q(tags__icontains=query),
            published=True
        )[:limit]
        results['tracks'] = TrackSerializer(tracks, many=True).data
    
    # Search users
    if search_type in ['users', 'all']:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(display_name__icontains=query) |
            Q(bio__icontains=query)
        )[:limit]
        results['users'] = UserSerializer(users, many=True).data
    
    return Response(results)


@api_view(['POST'])
def rebuild_search_index(request):
    # In Django, we don't need to rebuild an index as searches are done in real-time
    # This endpoint exists for API compatibility
    return Response({'success': True})
