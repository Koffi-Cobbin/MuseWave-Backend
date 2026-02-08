# Django Music Backend

A Django REST framework backend for a music streaming platform, providing a complete API for user management, track management, social features (likes, follows), and analytics.

## Features

- **User Management**: Create, read, update users with profiles and social links
- **Track Management**: Upload, manage, and publish music tracks
- **Social Features**: Like tracks, follow artists, comment on tracks
- **Analytics**: Track plays, downloads, user statistics, and engagement metrics
- **Search**: Full-text search for tracks and users
- **RESTful API**: Clean, well-documented REST endpoints

## Technology Stack

- **Django 5.0**: Web framework
- **Django REST Framework 3.14**: REST API framework
- **SQLite**: Database (easy to swap for PostgreSQL/MySQL)
- **Python 3.10+**: Programming language

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   cd django-music-backend
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (optional, for admin panel)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver 0.0.0.0:5000
   ```

The API will be available at `http://localhost:5000/musewave/`

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

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Accessing Admin Panel
Navigate to `http://localhost:5000/admin/` and log in with your superuser credentials.

## Production Deployment

1. **Set DEBUG=False in settings**
2. **Configure a production database** (PostgreSQL recommended)
3. **Set a strong SECRET_KEY**
4. **Configure ALLOWED_HOSTS**
5. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```
6. **Use a production server** (Gunicorn, uWSGI)
7. **Set up a reverse proxy** (Nginx, Apache)
8. **Enable HTTPS**

### Example with Gunicorn

```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:5000
```

## API Compatibility

This Django backend is designed to be a drop-in replacement for the Express/TypeScript backend, maintaining the same API endpoints and response formats.

### Key Differences from Express Backend

1. **Database**: Uses Django ORM with SQLite (vs JSON files)
2. **Better Performance**: Database queries are optimized with indexes
3. **Admin Interface**: Built-in Django admin for data management
4. **Type Safety**: Python type hints (vs TypeScript)
5. **Scalability**: Easier to scale with proper database

### Migration Notes

- All endpoint paths are identical
- Response formats match the original API
- Query parameters work the same way
- Request body structures are unchanged

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Use a different port
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Database migrations error**
   ```bash
   # Reset migrations
   python manage.py migrate --run-syncdb
   ```

3. **CORS errors**
   - Ensure `django-cors-headers` is installed and configured
   - Check CORS_ALLOW_ALL_ORIGINS in settings

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue on the repository.
