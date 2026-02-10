# MuseWave Authentication System

Complete JWT-based authentication system for Django REST Framework with advanced security features.

## 📋 Features

### Core Authentication
- ✅ **JWT Token-based authentication** - Secure, stateless authentication
- ✅ **Login with username or email** - Flexible user identification
- ✅ **Token refresh mechanism** - Seamless session extension
- ✅ **Secure logout** - Token blacklisting on logout
- ✅ **Last login tracking** - Automatic timestamp updates

### Password Management
- ✅ **Password change** - Secure in-app password updates
- ✅ **Password reset via email** - Forgot password flow
- ✅ **Password strength validation** - Django's built-in validators
- ✅ **Token-based reset** - Secure, time-limited reset links

### Security Features
- ✅ **Rate limiting** - 5 attempts per 15 minutes (configurable)
- ✅ **Account lockout** - Automatic lockout after failed attempts
- ✅ **Token blacklisting** - Invalidate tokens on logout/password change
- ✅ **Authentication logging** - Track all auth attempts
- ✅ **Generic error messages** - Prevent user enumeration
- ✅ **IP tracking** - Monitor authentication sources

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install djangorestframework-simplejwt==5.3.1 PyJWT==2.8.0

# Or add to requirements.txt and run:
pip install -r requirements.txt
```

### 2. Add Files to Project

Copy these files to your `musewave/` directory:
- `auth_serializers.py`
- `auth_views.py`

### 3. Update Settings

Add to `config/settings.py`:

```python
from datetime import timedelta

INSTALLED_APPS = [
    # ... existing apps
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    # ... rest of apps
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # ... your other settings
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# Email (development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'MuseWave <noreply@musewave.com>'
FRONTEND_URL = 'http://localhost:3000'

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

### 4. Update URLs

Add to `musewave/urls.py`:

```python
from . import auth_views

urlpatterns = [
    # Authentication
    path('users/login/', auth_views.login_view, name='login'),
    path('users/logout/', auth_views.logout_view, name='logout'),
    path('users/refresh/', auth_views.token_refresh_view, name='token_refresh'),
    path('users/verify-token/', auth_views.verify_token_view, name='verify_token'),
    
    # Password management
    path('users/password/change/', auth_views.change_password_view, name='change_password'),
    path('users/password/reset/', auth_views.password_reset_request_view, name='password_reset_request'),
    path('users/password/reset/confirm/', auth_views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # ... your existing URLs
]
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Test

```bash
chmod +x test_auth_api.sh
./test_auth_api.sh
```

## 📚 API Documentation

### Login

**Endpoint:** `POST /api/users/login/`

**Request:**
```json
{
  "username_or_email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "testuser",
    "email": "test@example.com"
  },
  "message": "Login successful"
}
```

### Logout

**Endpoint:** `POST /api/users/logout/`

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "refresh": "refresh_token_here"
}
```

### Refresh Token

**Endpoint:** `POST /api/users/refresh/`

**Request:**
```json
{
  "refresh": "refresh_token_here"
}
```

### Change Password

**Endpoint:** `POST /api/users/password/change/`

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{
  "old_password": "current_password",
  "new_password": "new_password123",
  "new_password_confirm": "new_password123"
}
```

### Password Reset Request

**Endpoint:** `POST /api/users/password/reset/`

**Request:**
```json
{
  "email": "user@example.com"
}
```

### Password Reset Confirm

**Endpoint:** `POST /api/users/password/reset/confirm/`

**Request:**
```json
{
  "uid": "MQ",
  "token": "reset-token-from-email",
  "new_password": "new_password123",
  "new_password_confirm": "new_password123"
}
```

## 🔒 Security Configuration

### Rate Limiting

Default: 5 attempts per 15 minutes

To modify, edit `auth_views.py`:

```python
def check_rate_limit(identifier, max_attempts=10, window_minutes=30):
    # Your custom limits
    pass
```

### Token Lifetime

Modify in `settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),  # Longer access
    'REFRESH_TOKEN_LIFETIME': timedelta(days=14),  # Longer refresh
}
```

### Password Validation

Customize in `settings.py`:

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Stronger requirement
    },
    # ... other validators
]
```

## 🧪 Testing

### Create Test User

```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

### Test Login

```bash
curl -X POST http://localhost:5000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

### Test Protected Endpoint

```bash
curl -X GET http://localhost:5000/api/users/verify-token/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🌐 Frontend Integration

### JavaScript/React Example

```javascript
// Store tokens after login
const login = async (email, password) => {
  const response = await fetch('/api/users/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username_or_email: email,
      password: password
    })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.token.access);
  localStorage.setItem('refresh_token', data.token.refresh);
  return data.user;
};

// Make authenticated requests
const apiCall = async (url, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.status === 401) {
    // Token expired, refresh
    await refreshToken();
    return apiCall(url, options); // Retry
  }
  
  return response.json();
};

// Refresh token
const refreshToken = async () => {
  const refresh = localStorage.getItem('refresh_token');
  
  const response = await fetch('/api/users/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh })
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
};
```

## 📊 File Structure

```
musewave/
├── auth_serializers.py      # Authentication serializers
├── auth_views.py             # Authentication views
├── models.py                 # User model (existing)
├── urls.py                   # URL patterns (updated)
└── ...
```

## 🚨 Common Issues

### Issue: "Token blacklist not found"

**Solution:**
```bash
python manage.py migrate
```

### Issue: Emails not sending

**Development:** Check console output
**Production:** Configure SMTP in settings.py

### Issue: CORS errors

**Solution:**
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]
```

## 📖 Additional Documentation

- `AUTH_INSTALLATION_GUIDE.md` - Detailed installation steps
- `PRODUCTION_DEPLOYMENT.md` - Production deployment guide
- `test_auth_api.sh` - Automated API testing

## 🤝 Support

For issues or questions:
1. Check documentation
2. Review error logs: `/var/log/musewave/auth.log`
3. Test with provided curl commands

## 📝 License

MIT License - Same as MuseWave project

## 🎉 Credits

Built for MuseWave Django Backend
