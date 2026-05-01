# MuseWave — Django Music Backend

A Django REST Framework backend for a music streaming platform. Provides a complete API for user management, track and album management, file uploads, social features, and analytics.

## Features

- **User Management** — Register, authenticate, and manage user profiles with avatar/header images
- **Track Management** — Upload and publish music tracks with audio files and cover art
- **Album Management** — Group tracks into albums with cover art
- **File Storage** — File uploads (audio, images) are handled by the external [FileForge](https://fileforge1.pythonanywhere.com) service
- **Social Features** — Like tracks, follow artists, comment on tracks, playlist management
- **Analytics** — Play tracking, download counts, user statistics, and engagement metrics
- **Search** — Full-text search across tracks and users
- **JWT Authentication** — Secure token-based auth with refresh token rotation

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 5.0.1 |
| API | Django REST Framework 3.14 |
| Auth | `djangorestframework-simplejwt` |
| Database | SQLite (dev) — PostgreSQL/MySQL ready |
| File Storage | FileForge (external service) |
| Background Tasks | `django-q2` (ORM-backed, no Redis needed) |
| Cache | Django database cache |

## Project Structure

```
musewave/
├── config/                  # Django project config
│   ├── settings.py          # Settings (env-driven)
│   ├── urls.py              # Root URL routing
│   └── wsgi.py
├── musewave/                # Core app
│   ├── models.py            # User, Track, Album, Playlist, Like, Follow, …
│   ├── views.py             # API view functions
│   ├── serializers.py       # DRF serializers (read + write)
│   ├── auth_views.py        # Login, logout, token refresh
│   ├── stream_views.py      # Audio stream redirect
│   ├── middleware.py        # Request logging
│   └── services/
│       └── fileforge.py     # FileForge API client
├── manage.py
├── requirements.txt
└── API_ENDPOINTS.md         # Full endpoint reference
```

## Installation

### Prerequisites

- Python 3.12
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd django-music-backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables** (see [Environment Variables](#environment-variables))

4. **Run migrations**
   ```bash
   python manage.py migrate
   python manage.py createcachetable
   ```

5. **Create a superuser** (optional — for the admin panel)
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver 0.0.0.0:5000
   ```

The API is available at `http://localhost:5000/api/`.

## Environment Variables

Create a `.env` file in the project root or set these in your environment:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | Insecure dev key |
| `DEBUG` | Enable debug mode | `True` |
| `FILEFORGE_API_KEY` | API key from the FileForge developer console | `ffk_dummy_key_replace_me` |
| `FILEFORGE_BASE_URL` | FileForge service base URL | `https://fileforge1.pythonanywhere.com` |
| `EMAIL_HOST` | SMTP host for verification emails | — |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP username | — |
| `EMAIL_HOST_PASSWORD` | SMTP password | — |
| `DEFAULT_FROM_EMAIL` | From address for outgoing emails | `EMAIL_HOST_USER` |

## File Storage — FileForge

All file uploads (audio, cover images, user avatars and headers) are routed through the **FileForge** service at `https://fileforge1.pythonanywhere.com`.

### How it works

1. The client sends a `multipart/form-data` request with the file field alongside the normal JSON fields.
2. MuseWave uploads the file to FileForge in **sync mode** and receives a CDN URL immediately.
3. The URL and the FileForge file ID are stored in the database.
4. When a track or album is deleted, the associated files are automatically removed from FileForge.

### File fields

| Resource | File field | URL stored on model |
|---|---|---|
| User | `avatar_file` (image) | `avatar_url` |
| User | `header_file` (image) | `header_url` |
| Track | `audio_file` (any) | `audio_url` |
| Track | `cover_file` (image) | `cover_url` |
| Album | `cover_file` (image) | `cover_url` |

Clients that already have a hosted URL can pass it directly (e.g. `"audio_url": "https://..."`) and skip the file upload.

### FileForge client

The client lives at `musewave/services/fileforge.py` and exposes:

```python
from musewave.services.fileforge import upload_file, delete_file, health

# Upload a file (returns the FileForge record dict)
record = upload_file(file_obj, "track_audio.mp3")
url    = record["url"]
fid    = record["id"]

# Delete a file by its FileForge ID
delete_file(fid)

# Check service health
health()  # {"status": "ok", "providers": ["cloudinary", "google_drive"]}
```

## API Endpoints

All endpoints are prefixed with `/api/`. See `API_ENDPOINTS.md` for the full reference.

### Authentication

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/users/login` | Login — returns JWT access + refresh tokens |
| `POST` | `/api/users/logout` | Logout (blacklists refresh token) |
| `POST` | `/api/users/refresh` | Refresh access token |
| `GET` | `/api/users/verify-token` | Verify an access token |
| `POST` | `/api/users/password/change` | Change password |
| `POST` | `/api/users/password/reset` | Request password reset email |
| `POST` | `/api/users/password/reset/confirm` | Confirm password reset |

### Users

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/users` | List users (auth required) |
| `POST` | `/api/users/create` | Register a new user |
| `GET` | `/api/users/<id>` | Public profile |
| `GET` | `/api/users/<id>/me` | Own full profile (auth required) |
| `PATCH` | `/api/users/<id>/update` | Update profile / upload avatar or header |
| `GET` | `/api/users/username/<username>` | Look up by username |
| `GET` | `/api/users/<id>/stats` | User statistics |
| `GET` | `/api/users/<id>/likes` | Liked tracks |
| `GET` | `/api/users/<id>/plays` | Play history |
| `GET` | `/api/users/<id>/albums` | User albums |
| `POST` | `/api/users/<id>/follow` | Follow a user |
| `DELETE` | `/api/users/<id>/follow` | Unfollow a user |
| `GET` | `/api/users/<id>/followers` | List followers |
| `GET` | `/api/users/<id>/following` | List following |

### Tracks

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/tracks` | List tracks (filters: `userId`, `genre`, `mood`, `tags`, `published`, `sortBy`, `sortOrder`) |
| `POST` | `/api/tracks/create` | Create a track (multipart — include `audio_file` and optionally `cover_file`) |
| `GET` | `/api/tracks/<id>` | Get track |
| `PATCH` | `/api/tracks/<id>` | Update track |
| `DELETE` | `/api/tracks/<id>` | Delete track (removes files from FileForge) |
| `GET` | `/api/tracks/<id>/stream/` | Returns `audio_url` for client-side streaming |
| `GET` | `/api/tracks/<id>/stream-url/` | Returns stream metadata + URL |
| `GET` | `/api/tracks/<id>/download/` | Record a download and return audio URL |
| `GET` | `/api/tracks/<id>/stats` | Track statistics |
| `POST` | `/api/tracks/<id>/like` | Like a track |
| `DELETE` | `/api/tracks/<id>/like` | Unlike a track |
| `POST` | `/api/tracks/<id>/play` | Record a play event |
| `POST` | `/api/tracks/<id>/download` | Record a download |

### Albums

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/albums` | Create an album (multipart — include `cover_file` optionally) |
| `GET` | `/api/albums/<id>` | Get album |
| `PATCH` | `/api/albums/<id>/update` | Update album |
| `DELETE` | `/api/albums/<id>/delete` | Delete album (tracks remain, association removed) |

### Playlists

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/playlists` | List playlists (auth required) |
| `POST` | `/api/playlists` | Create a playlist |
| `GET` | `/api/playlists/<id>` | Get playlist with tracks |
| `PATCH` | `/api/playlists/<id>` | Update playlist |
| `DELETE` | `/api/playlists/<id>` | Delete playlist |
| `POST` | `/api/playlists/<id>/add-track` | Add a track |
| `POST` | `/api/playlists/<id>/remove-track` | Remove a track |
| `POST` | `/api/playlists/<id>/reorder` | Reorder tracks |

### Search & Artists

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/search?q=<query>&type=tracks\|users\|all` | Search tracks and/or users |
| `GET` | `/api/artists` | List artists (users with published tracks) |

## Request / Response Examples

### Register a User

```bash
POST /api/users/create
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword123",
  "display_name": "John Doe",
  "bio": "Music producer and DJ"
}
```

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "display_name": "John Doe",
  "verified": false,
  "message": "Account created successfully! Please check your email to verify your account.",
  "verification_required": true
}
```

### Create a Track (with file upload)

```bash
POST /api/tracks/create
Content-Type: multipart/form-data

user_id=<uuid>
title=Summer Vibes
artist=John Doe
artist_slug=john-doe
genre=Electronic
audio_duration=240.5
published=true
audio_file=@summer-vibes.mp3     # uploaded to FileForge
cover_file=@cover.jpg            # uploaded to FileForge
```

```json
{
  "id": "track-uuid",
  "title": "Summer Vibes",
  "artist": "John Doe",
  "audio_url": "https://res.cloudinary.com/.../summer-vibes.mp3",
  "cover_url": "https://res.cloudinary.com/.../cover.jpg",
  "audio_duration": 240.5,
  "published": true
}
```

Or pass URLs directly without uploading a file:

```json
{
  "user_id": "...",
  "title": "Summer Vibes",
  "artist": "John Doe",
  "artist_slug": "john-doe",
  "genre": "Electronic",
  "audio_url": "https://cdn.example.com/tracks/summer-vibes.mp3",
  "audio_duration": 240.5,
  "published": true
}
```

### Update User Avatar

```bash
PATCH /api/users/<id>/update
Authorization: Bearer <token>
Content-Type: multipart/form-data

avatar_file=@new-avatar.jpg
```

## Database Models

### User
- `username`, `email`, `display_name`, `bio`
- `avatar_url`, `avatar_fileforge_id`
- `header_url`, `header_fileforge_id`
- Social links: `twitter`, `instagram`, `spotify`, `soundcloud`
- `verified`, `is_active`, `is_staff`

### Track
- `title`, `artist`, `artist_slug`, `description`, `genre`, `mood`, `tags`
- `audio_url`, `audio_fileforge_id`, `audio_file_size`, `audio_duration`, `audio_format`
- `cover_url`, `cover_fileforge_id`, `cover_gradient`, `waveform_data`
- `bpm`, `key`
- Stats: `plays`, `likes`, `downloads`, `shares`
- `published`, `published_at`

### Album
- `title`, `artist`, `description`, `genre`
- `cover_url`, `cover_fileforge_id`, `cover_gradient`
- `release_date`, `published`

### Supporting models
- **Like** — user × track
- **Play** — user × track + duration, completed flag
- **Download** — user × track + ip/user-agent
- **Follow** — follower × following
- **Playlist / PlaylistTrack** — user playlists with ordered tracks
- **Comment** — user × track + timestamp

## Development

### Run the server
```bash
python manage.py runserver 0.0.0.0:5000
```

### Create migrations after model changes
```bash
python manage.py makemigrations
python manage.py migrate
```

### Admin panel
Navigate to `http://localhost:5000/admin/` and log in with superuser credentials.

### Check FileForge connectivity
```bash
python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()
from musewave.services.fileforge import health
print(health())
"
```

## Production Deployment

The project is pre-configured for Replit autoscale deployment using Gunicorn:

```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=2 config.wsgi:application
```

For other environments:

1. Set `DEBUG=False`
2. Set a strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS`
4. Set `FILEFORGE_API_KEY` to a real key from the FileForge developer console
5. Configure SMTP variables for email verification
6. Use PostgreSQL for production (`DATABASES` in `settings.py`)
7. Run `python manage.py collectstatic`
8. Serve static files via Nginx or a CDN

## License

MIT License
