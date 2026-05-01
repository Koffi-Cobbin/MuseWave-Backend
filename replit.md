# MuseWave Django Backend

A Django REST API for a music streaming platform. This backend provides RESTful endpoints for managing users, tracks, albums, playlists, likes, follows, and file streaming.

## Tech Stack

- **Language:** Python 3.12
- **Framework:** Django 5.0.1 + Django REST Framework 3.14
- **Authentication:** JWT via `djangorestframework-simplejwt`
- **Database:** SQLite (dev) — compatible with PostgreSQL/MySQL for production
- **Background Tasks:** `django-q2` (ORM-backed, no Redis needed)
- **File Storage:** Google Drive API (`google-api-python-client`)
- **Cache:** Django database cache (`django_cache` table)

## Project Structure

- `config/` — Django project settings, root URLs, WSGI/ASGI entry points
- `musewave/` — Core app: models, views, serializers, auth, streaming, middleware
- `fileforge/` — File management app: Google Drive integration, background upload tasks
- `manage.py` — Django management utility
- `API_ENDPOINTS.md` — Full API documentation

## Running Locally

The app runs via the "Start application" workflow on port 5000:

```
python manage.py runserver 0.0.0.0:5000
```

## Environment Variables

The following environment variables are required for full functionality (optional for dev):

- `SECRET_KEY` — Django secret key
- `DEBUG` — Set to `True` for development
- `GOOGLE_CLIENT_ID` — Google OAuth2 client ID
- `GOOGLE_CLIENT_SECRET` — Google OAuth2 client secret
- `GOOGLE_REFRESH_TOKEN` — Google OAuth2 refresh token
- `GOOGLE_DRIVE_ROOT_FOLDER_ID` — Root Google Drive folder for file uploads
- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — SMTP email settings

## Key API Endpoints

All routes are prefixed with `/api/`:

- `POST /api/auth/register` — Register new user
- `POST /api/auth/login` — Login and get JWT tokens
- `GET /api/tracks` — List tracks
- `GET /api/albums` — List albums
- `GET /api/playlists` — List playlists
- `GET /api/fileforge/files/<id>/stream/` — Stream audio file

See `API_ENDPOINTS.md` for the complete API reference.

## Deployment

Configured for Replit autoscale deployment using Gunicorn:

```
gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=2 config.wsgi:application
```
