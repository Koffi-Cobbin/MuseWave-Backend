# MuseWave Django Backend

A Django REST API for a music streaming platform. Provides RESTful endpoints for managing users, tracks, albums, playlists, likes, follows, and more.

## File Storage

File uploads (audio, cover images, avatars, headers) are handled by the external **FileForge** service at `https://fileforge1.pythonanywhere.com`. Files are uploaded via FileForge's REST API and the returned CDN URL is stored in the database. FileForge IDs are also stored per resource so files can be deleted from the provider when records are removed.

The client lives at `musewave/services/fileforge.py`.

## Tech Stack

- **Language:** Python 3.12
- **Framework:** Django 5.0.1 + Django REST Framework 3.14
- **Authentication:** JWT via `djangorestframework-simplejwt`
- **Database:** SQLite (dev) — compatible with PostgreSQL/MySQL for production
- **Background Tasks:** `django-q2` (ORM-backed, no Redis needed)
- **Cache:** Django database cache (`django_cache` table)

## Project Structure

- `config/` — Django project settings, root URLs, WSGI/ASGI entry points
- `musewave/` — Core app: models, views, serializers, auth, middleware
- `manage.py` — Django management utility
- `API_ENDPOINTS.md` — Full API documentation

## Models

- **User** — Custom user with `avatar_url`, `header_url`, social links
- **Track** — Music track with `audio_url`, `cover_url`, metadata
- **Album** — Album with `cover_url`, linked tracks
- **Playlist / PlaylistTrack** — User playlists
- **Like, Play, Download, Follow, Comment** — Activity/engagement models

All file references (audio, covers, avatars) are stored as plain URL fields. File hosting is handled externally.

## Running Locally

The app runs via the "Start application" workflow on port 5000:

```
python manage.py runserver 0.0.0.0:5000
```

## Environment Variables

- `FILEFORGE_API_KEY` — API key from the FileForge developer console (currently uses dummy default `ffk_dummy_key_replace_me`)
- `FILEFORGE_BASE_URL` — Override the FileForge service base URL (default: `https://fileforge1.pythonanywhere.com`)
- `SECRET_KEY` — Django secret key
- `DEBUG` — Set to `True` for development
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — SMTP email settings

## Key API Endpoints

All routes are prefixed with `/api/`:

- `POST /api/users/create` — Register new user
- `POST /api/users/login` — Login and get JWT tokens
- `GET /api/tracks` — List tracks
- `POST /api/tracks/create` — Create a track (with `audio_url`)
- `GET /api/albums` — List albums
- `GET /api/playlists` — List playlists

See `API_ENDPOINTS.md` for the complete API reference.

## Deployment

Configured for Replit autoscale deployment using Gunicorn:

```
gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=2 config.wsgi:application
```
