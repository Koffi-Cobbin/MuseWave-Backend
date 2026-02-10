from django.urls import path, re_path
from . import views
from . import auth_views


urlpatterns = [
    # Authentication
    path('users/login', auth_views.login_view, name='login'),
    path('users/logout', auth_views.logout_view, name='logout'),
    path('users/refresh', auth_views.token_refresh_view, name='token_refresh'),
    path('users/verify-token', auth_views.verify_token_view, name='verify_token'),
    
    # Password management
    path('users/password/change', auth_views.change_password_view, name='change_password'),
    path('users/password/reset', auth_views.password_reset_request_view, name='password_reset_request'),
    path('users/password/reset/confirm', auth_views.password_reset_confirm_view, name='password_reset_confirm'),

    # Users - Order matters! More specific routes first
    path('users/username/<str:username>', views.get_user_by_username, name='get_user_by_username'),
    path('users', views.users_list_or_create, name='users_list_or_create'),  # GET/POST
    path('users/<uuid:user_id>/stats', views.get_user_stats, name='get_user_stats'),
    path('users/<uuid:user_id>/likes', views.get_user_likes, name='get_user_likes'),
    path('users/<uuid:user_id>/plays', views.get_user_plays, name='get_user_plays'),
    path('users/<uuid:user_id>/albums', views.get_user_albums, name='get_user_albums'),
    path('users/<uuid:user_id>/follow', views.follow_user, name='follow_user'),  # POST/DELETE
    path('users/<uuid:user_id>/follow/<uuid:follower_id>', views.check_follow, name='check_follow'),
    path('users/<uuid:user_id>/followers', views.get_followers, name='get_followers'),
    path('users/<uuid:user_id>/following', views.get_following, name='get_following'),
    path('users/<uuid:user_id>', views.get_or_update_user, name='user_detail'),  # GET/PATCH
    
    # Artists
    path('artists', views.get_artists, name='get_artists'),
    
    # Albums
    path('albums', views.create_album, name='create_album'),  # POST
    path('albums/<uuid:album_id>', views.get_album, name='get_album'),  # GET
    path('albums/<uuid:album_id>/update', views.update_album, name='update_album'),  # PATCH
    path('albums/<uuid:album_id>/delete', views.delete_album, name='delete_album'),  # DELETE
    
    # Tracks
    path('tracks', views.tracks_list_or_create, name='tracks_list_or_create'),  # GET/POST
    path('tracks/<uuid:track_id>/stats', views.get_track_stats, name='get_track_stats'),
    path('tracks/<uuid:track_id>/like', views.like_track, name='like_track'),  # POST/DELETE
    path('tracks/<uuid:track_id>/like/<uuid:user_id>', views.check_like, name='check_like'),
    path('tracks/<uuid:track_id>/download', views.create_download, name='create_download'),
    path('tracks/<uuid:track_id>/downloads', views.get_track_downloads, name='get_track_downloads'),
    path('tracks/<uuid:track_id>/play', views.create_play, name='create_play'),
    path('tracks/<uuid:track_id>/plays', views.get_track_plays, name='get_track_plays'),
    path('tracks/<uuid:track_id>', views.track_detail, name='track_detail'),  # GET/PATCH/DELETE
    
    # Search
    path('search/rebuild', views.rebuild_search_index, name='rebuild_search_index'),
    path('search', views.search, name='search'),
]
