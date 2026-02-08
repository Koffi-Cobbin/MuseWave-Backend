# Folder Structure - Naming Convention

## 📁 Folder Names Update

The Django backend uses clean, descriptive folder names that clearly indicate their purpose:

### Project Structure

```
django-music-backend/
├── config/          # Django project configuration
└── musewave/        # Main application (MuseWave API)
```

### Folder Naming Rationale

#### `config/` (Project Configuration)
- **Purpose:** Django project configuration and settings
- **Contains:** settings.py, urls.py, wsgi.py, asgi.py
- **Clarity:** Immediately clear this is the configuration folder
- **Standard:** Common in Django projects for cleaner naming

**What's in config/:**
- `settings.py` - All Django settings (database, middleware, apps)
- `urls.py` - Root URL routing
- `wsgi.py` - WSGI application for deployment
- `asgi.py` - ASGI application for async support

#### `musewave/` (Main Application)
- **Purpose:** The MuseWave music platform API
- **Contains:** models, views, serializers, URLs, admin
- **Clarity:** Application name matches project branding
- **Organization:** All API logic in one clear location

**What's in musewave/:**
- `models.py` - Database models (User, Track, Album, etc.)
- `views.py` - API endpoint handlers
- `serializers.py` - Data validation and serialization
- `urls.py` - API URL routing
- `admin.py` - Django admin configuration
- `middleware.py` - Custom middleware
- `exceptions.py` - Error handling
- `management/` - Custom commands

### Comparison with Previous Names

| Old Name | New Name | Purpose |
|----------|----------|---------|
| `music_backend/` | `config/` | Project configuration |
| `api/` | `musewave/` | Main application |

### Benefits of New Names

1. **Clarity:** Immediately understand what each folder contains
2. **Professionalism:** Clean, branded naming (MuseWave)
3. **Standards:** Follows Django best practices
4. **Scalability:** Easy to add more apps alongside musewave
5. **Branding:** Application name matches product name

### Import Examples

**Before (old structure):**
```python
from api.models import User, Track
from music_backend import settings
```

**After (new structure):**
```python
from musewave.models import User, Track
from config import settings
```

### Environment Variables

**Before:**
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'music_backend.settings')
```

**After:**
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
```

### URL Configuration

**Before:**
```python
ROOT_URLCONF = 'music_backend.urls'
```

**After:**
```python
ROOT_URLCONF = 'config.urls'
```

### WSGI/ASGI Application

**Before:**
```python
WSGI_APPLICATION = 'music_backend.wsgi.application'
```

**After:**
```python
WSGI_APPLICATION = 'config.wsgi.application'
```

### Installed Apps

**Before:**
```python
INSTALLED_APPS = [
    # ...
    'api',
]
```

**After:**
```python
INSTALLED_APPS = [
    # ...
    'musewave',
]
```

### All Updated References

The following files have been updated to use the new folder names:

#### Python Files
- ✅ `manage.py`
- ✅ `config/settings.py`
- ✅ `config/urls.py`
- ✅ `config/wsgi.py`
- ✅ `config/asgi.py`
- ✅ `musewave/apps.py`
- ✅ `musewave/management/commands/seed_data.py`

#### Scripts
- ✅ `check_files.sh`
- ✅ `quickstart.sh`

#### Documentation
- ✅ `README.md`
- ✅ `PROJECT_SUMMARY.md`
- ✅ `MIGRATION_GUIDE.md`
- ✅ `FILE_STRUCTURE.md`
- ✅ `START_HERE.md`
- ✅ `CHANGELOG.md`
- ✅ `ALBUM_FEATURE_GUIDE.md`
- ✅ `UPDATE_SUMMARY.md`

### No Action Required

The folder renaming is **complete and transparent**. All references have been updated. Simply:

1. Extract the zip file
2. Run migrations
3. Start the server

Everything works out of the box with the new, cleaner folder structure!

### Command Reference

All commands remain the same, just with clearer folder names internally:

```bash
# Start server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Custom commands
python manage.py seed_data
python manage.py createsuperuser

# Deploy with gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:5000
```

### Directory Navigation

```bash
# Configuration files
cd config/
ls  # settings.py, urls.py, wsgi.py, asgi.py

# Application code
cd musewave/
ls  # models.py, views.py, serializers.py, urls.py, admin.py

# Management commands
cd musewave/management/commands/
ls  # seed_data.py
```

### Testing

All tests continue to work with the new structure:

```bash
python manage.py test musewave
```

### Summary

✅ **Cleaner structure:** config/ and musewave/
✅ **All files updated:** No manual changes needed
✅ **Fully functional:** Ready to use immediately
✅ **Professional naming:** Branded application name
✅ **Best practices:** Follows Django conventions

The new folder names make the project structure immediately clear and professional!
