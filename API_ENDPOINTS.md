# Django Music Backend

A Django REST framework backend for a music streaming platform, providing a complete API for user management, track management, social features (likes, follows), and analytics.
Database is SQLite.

## Features

- **User Management**: Create, read, update users with profiles and social links
- **Track Management**: Upload, manage, and publish music tracks
- **Social Features**: Like tracks, follow artists, comment on tracks
- **Analytics**: Track plays, downloads, user statistics, and engagement metrics
- **Search**: Full-text search for tracks and users
- **RESTful API**: Clean, well-documented REST endpoints

## API Endpoints

### Users

- `GET /musewave/users/` - List all users (with pagination)
- `GET /musewave/users/<id>/` - Get user by ID
- `GET /musewave/users/username/<username>/` - Get user by username
- `POST /musewave/users/create/` - Create a new user
- `PATCH /musewave/users/<id>/update/` - Update user
- `GET /musewave/users/<id>/stats/` - Get user statistics

### Tracks

- `GET /musewave/tracks/` - List tracks (with filters: userId, genre, mood, tags, published)
- `GET /musewave/tracks/<id>/` - Get track by ID
- `POST /musewave/tracks/create/` - Create a new track
- `PATCH /musewave/tracks/<id>/update/` - Update track
- `DELETE /musewave/tracks/<id>/delete/` - Delete track
- `GET /musewave/tracks/<id>/stats/` - Get track statistics

### Albums

- `GET /musewave/users/<user_id>/albums` - Get all albums for a user
- `GET /musewave/albums/<id>` - Get album by ID (includes tracks)
- `POST /musewave/albums` - Create a new album (with track associations)
- `PATCH /musewave/albums/<id>/update` - Update album
- `DELETE /musewave/albums/<id>/delete` - Delete album (tracks remain, album association removed)

### Playlists

- `GET /musewave/playlists/` - List user's playlists
- `POST /musewave/playlists/` - Create a new playlist
- `GET /musewave/playlists/<id>/` - Get playlist details (includes tracks)
- `PATCH /musewave/playlists/<id>/` - Update playlist (rename)
- `DELETE /musewave/playlists/<id>/` - Delete playlist
- `POST /musewave/playlists/<id>/add_track/` - Add track to playlist
- `POST /musewave/playlists/<id>/remove_track/` - Remove track from playlist
- `POST /musewave/playlists/<id>/reorder/` - Reorder tracks in playlist

### Likes

- `POST /musewave/tracks/<track_id>/like/` - Like a track
- `DELETE /musewave/tracks/<track_id>/like/delete/` - Unlike a track
- `GET /musewave/tracks/<track_id>/like/<user_id>/` - Check if user liked track
- `GET /musewave/users/<user_id>/likes/` - Get user's liked tracks

### Downloads

- `POST /musewave/tracks/<track_id>/download/` - Record a download
- `GET /musewave/tracks/<track_id>/downloads/` - Get track downloads

### Plays

- `POST /musewave/tracks/<track_id>/play/` - Record a play
- `GET /musewave/tracks/<track_id>/plays/` - Get track plays
- `GET /musewave/users/<user_id>/plays/` - Get user's play history

### Follows

- `POST /musewave/users/<user_id>/follow/` - Follow a user
- `DELETE /musewave/users/<user_id>/follow/delete/` - Unfollow a user
- `GET /musewave/users/<user_id>/follow/<follower_id>/` - Check if following
- `GET /musewave/users/<user_id>/followers/` - Get user's followers
- `GET /musewave/users/<user_id>/following/` - Get users being followed

### Search

- `GET /musewave/search/?q=<query>&type=<tracks|users|all>&limit=<number>` - Search
- `POST /musewave/search/rebuild/` - Rebuild search index (no-op in Django)

### Artists

- `GET /musewave/artists/` - Get all users who have published tracks

## Request/Response Examples

### Create a User

**Request:**
```bash
POST /musewave/users/create/
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "display_name": "John Doe",
  "bio": "Music producer and DJ"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "display_name": "John Doe",
  "bio": "Music producer and DJ",
  "verified": false,
  "created_at": "2024-02-04T10:30:00Z",
  "updated_at": "2024-02-04T10:30:00Z"
}
```

### Create a Track

**Request:**
```bash
POST /musewave/tracks/create/
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Summer Vibes",
  "artist": "John Doe",
  "artist_slug": "john-doe",
  "genre": "Electronic",
  "mood": "Happy",
  "tags": ["summer", "dance", "upbeat"],
  "audio_url": "https://example.com/tracks/summer-vibes.mp3",
  "audio_file_size": 5242880,
  "audio_duration": 240.5,
  "audio_format": "mp3",
  "published": true
}
```

### Create an Album

**Request:**
```bash
POST /musewave/albums
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Summer Collection",
  "artist": "John Doe",
  "genre": "Electronic",
  "description": "A collection of summer hits",
  "release_date": "2024-06-01T00:00:00Z",
  "published": true,
  "track_ids": [
    "track-uuid-1",
    "track-uuid-2",
    "track-uuid-3"
  ]
}
```

**Response:**
```json
{
  "id": "album-uuid",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Summer Collection",
  "artist": "John Doe",
  "genre": "Electronic",
  "description": "A collection of summer hits",
  "release_date": "2024-06-01T00:00:00Z",
  "published": true,
  "track_count": 3,
  "created_at": "2024-02-04T10:30:00Z",
  "updated_at": "2024-02-04T10:30:00Z"
}
```

### Create a Playlist

**Request:**
```bash
POST /musewave/playlists/
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "name": "My Favorite Tracks",
  "description": "A collection of my favorite songs",
  "public": true
}
```

**Response:**
```json
{
  "id": "playlist-uuid",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Favorite Tracks",
  "description": "A collection of my favorite songs",
  "public": true,
  "tracks_count": 0,
  "track_ids": [],
  "created_at": "2024-02-04T10:30:00Z",
  "updated_at": "2024-02-04T10:30:00Z"
}
```

### Add Track to Playlist

**Request:**
```bash
POST /musewave/playlists/<playlist-id>/add_track/
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "track_id": "track-uuid-1"
}
```

**Response:**
```json
{
  "id": "playlist-track-uuid",
  "track_id": "track-uuid-1",
  "track": {
    "id": "track-uuid-1",
    "title": "Summer Vibes",
    "artist": "John Doe",
    "audio_url": "https://example.com/tracks/summer-vibes.mp3",
    "audio_duration": 240.5
  },
  "order": 0,
  "added_at": "2024-02-04T10:35:00Z"
}
```

### Reorder Playlist Tracks

**Request:**
```bash
POST /musewave/playlists/<playlist-id>/reorder/
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

[
  {"id": "playlist-track-uuid-1", "order": 1},
  {"id": "playlist-track-uuid-2", "order": 0},
  {"id": "playlist-track-uuid-3", "order": 2}
]
```

**Response:**
```json
{
  "success": true
}
```

### List Tracks with Filters

**Request:**
```bash
GET /musewave/tracks/?genre=Electronic&published=true&sortBy=plays&sortOrder=desc&limit=10
```

### Search

**Request:**
```bash
GET /musewave/search/?q=summer&type=all&limit=20
```

**Response:**
```json
{
  "tracks": [...],
  "users": [...]
}
```

## Database Models

### User
- Basic info: username, email, password (hashed)
- Profile: display_name, bio, avatar_url, header_url
- Social links: twitter, instagram, spotify, soundcloud
- Metadata: verified, created_at, updated_at

### Album
- Info: title, artist, description, genre
- Media: cover_url, cover_gradient
- Metadata: release_date, published
- Relationships: user (owner), tracks (one-to-many)

### Track
- Info: title, artist, description, genre, mood, tags
- Audio: audio_url, file_size, duration, format
- Relationships: user (owner), album (optional)
- Media: cover_url, waveform_data
- Metadata: bpm, key
- Stats: plays, likes, downloads, shares
- Status: published, published_at

### Like
- References: user, track
- Timestamp: created_at

### Download
- References: user (optional), track
- Metadata: ip_address, user_agent
- Timestamp: created_at

### Play
- References: user (optional), track
- Data: duration, completed
- Metadata: ip_address, user_agent
- Timestamp: created_at

### Follow
- References: follower, following
- Timestamp: created_at

### Playlist
- Info: name, description, public
- Media: cover_url
- Relationships: user (owner), tracks (many-to-many through PlaylistTrack)
- Metadata: created_at, updated_at

### PlaylistTrack
- References: playlist, track
- Ordering: order (integer for track sequence)
- Timestamp: added_at

## Statistics & Analytics

The API provides comprehensive statistics:

### User Stats
- Total tracks uploaded
- Total plays across all tracks
- Total likes received
- Total downloads
- Follower/following counts
- Monthly unique listeners

### Track Stats
- Daily play counts
- Unique listener count
- Average listen duration
- Completion rate (% who listened to >80%)

## Sample API Usage

Here's a complete example of using the API to create a user, upload tracks, create a playlist, and manage it:

```bash
# 1. Create a user
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "musicfan",
    "email": "fan@example.com",
    "password": "password123",
    "display_name": "Music Fan"
  }'

# 2. Login to get JWT token
curl -X POST http://localhost:8000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "fan@example.com",
    "password": "password123"
  }'

# 3. Create tracks (assuming you have track data)
curl -X POST http://localhost:8000/api/tracks \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid",
    "title": "Awesome Song",
    "artist": "Music Fan",
    "genre": "Pop",
    "audio_url": "https://example.com/song.mp3",
    "audio_duration": 180,
    "published": true
  }'

# 4. Create a playlist
curl -X POST http://localhost:8000/api/playlists \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Playlist",
    "description": "My favorite songs",
    "public": true
  }'

# 5. Add tracks to playlist
curl -X POST http://localhost:8000/api/playlists/PLAYLIST_UUID/add_track \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "track_id": "track-uuid"
  }'

# 6. Get playlist with tracks
curl -X GET http://localhost:8000/api/playlists/PLAYLIST_UUID \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```
