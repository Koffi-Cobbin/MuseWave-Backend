# Authentication System - Installation & Migration Guide

## 📋 Overview

This guide walks you through adding complete authentication to your MuseWave Django backend, including:
- JWT-based login/logout
- Token refresh mechanism
- Password change functionality
- Password reset via email
- Rate limiting and security features

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd django-music-backend
source venv/bin/activate
pip install djangorestframework-simplejwt==5.3.1 PyJWT==2.8.0
```

### Step 2: Copy Files

Copy the authentication files to your project:

```bash
# Copy to musewave app directory
cp auth_serializers.py musewave/
cp auth_views.py musewave/

# Or manually create the files in musewave/ directory
```

### Step 3: Update Settings

Add to `config/settings.py`:

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    # ... rest of apps
]

# Update REST_FRAMEWORK settings
from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    # ... keep your existing settings
}

# Add JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Email settings (development - console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'MuseWave <noreply@musewave.com>'
FRONTEND_URL = 'http://localhost:3000'

# Caching for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### Step 4: Update URLs

Update `musewave/urls.py` to include authentication endpoints:

```python
from django.urls import path
from . import views
from . import auth_views  # ADD THIS

urlpatterns = [
    # Authentication endpoints - ADD THESE AT THE TOP
    path('users/login/', auth_views.login_view, name='login'),
    path('users/logout/', auth_views.logout_view, name='logout'),
    path('users/refresh/', auth_views.token_refresh_view, name='token_refresh'),
    path('users/verify-token/', auth_views.verify_token_view, name='verify_token'),
    path('users/password/change/', auth_views.change_password_view, name='change_password'),
    path('users/password/reset/', auth_views.password_reset_request_view, name='password_reset_request'),
    path('users/password/reset/confirm/', auth_views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # ... rest of your existing URLs
]
```

### Step 5: Run Migrations

```bash
python manage.py migrate
```

This creates the token blacklist tables.

### Step 6: Test the System

```bash
# Make the test script executable
chmod +x test_auth_api.sh

# Run tests
./test_auth_api.sh
```

## 📖 API Documentation

### 1. Login

**Endpoint:** `POST /api/users/login/`

**Request:**
```json
{
  "username_or_email": "user@example.com",
  "password": "password123"
}
```

**Success Response (200):**
```json
{
  "token": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "testuser",
    "email": "test@example.com",
    "display_name": "Test User",
    "verified": false
  },
  "message": "Login successful"
}
```

**Error Response (401):**
```json
{
  "error": "Invalid credentials",
  "status": 401,
  "attempts_remaining": 4
}
```

**Rate Limited (429):**
```json
{
  "error": "Too many login attempts. Please try again later.",
  "status": 429
}
```

### 2. Logout

**Endpoint:** `POST /api/users/logout/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "refresh": "refresh_token_here"
}
```

**Success Response (200):**
```json
{
  "message": "Logout successful"
}
```

### 3. Refresh Token

**Endpoint:** `POST /api/users/refresh/`

**Request:**
```json
{
  "refresh": "refresh_token_here"
}
```

**Success Response (200):**
```json
{
  "access": "new_access_token",
  "refresh": "new_refresh_token"
}
```

### 4. Change Password

**Endpoint:** `POST /api/users/password/change/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "old_password": "current_password",
  "new_password": "new_password123",
  "new_password_confirm": "new_password123"
}
```

**Success Response (200):**
```json
{
  "message": "Password changed successfully. Please login again.",
  "require_reauth": true
}
```

### 5. Password Reset Request

**Endpoint:** `POST /api/users/password/reset/`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "message": "If an account exists with this email, a password reset link has been sent."
}
```

### 6. Password Reset Confirm

**Endpoint:** `POST /api/users/password/reset/confirm/`

**Request:**
```json
{
  "uid": "MQ",
  "token": "actual-token-from-email",
  "new_password": "new_password123",
  "new_password_confirm": "new_password123"
}
```

**Success Response (200):**
```json
{
  "message": "Password has been reset successfully. You can now login with your new password."
}
```

### 7. Verify Token

**Endpoint:** `GET /api/users/verify-token/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "valid": true,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

## 🔒 Security Features

### 1. Rate Limiting
- Maximum 5 failed login attempts per 15 minutes
- Prevents brute force attacks
- Tracked by IP + username combination

### 2. Token Blacklisting
- Logout invalidates refresh tokens
- Password change requires re-authentication
- Tokens cannot be reused after blacklisting

### 3. Password Validation
- Minimum 8 characters
- Cannot be too similar to user information
- Cannot be a commonly used password
- Cannot be entirely numeric

### 4. Secure Error Messages
- Generic "Invalid credentials" message
- Doesn't reveal if username/email exists
- Prevents user enumeration

### 5. Authentication Logging
- All login attempts logged
- Success and failure tracking
- IP address and user agent recording

## 🧪 Testing Examples

### Test Successful Login
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

### Test Password Change
```bash
curl -X POST http://localhost:5000/api/users/password/change/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "CurrentPass123!",
    "new_password": "NewPass456!",
    "new_password_confirm": "NewPass456!"
  }'
```

### Test Rate Limiting
```bash
# Run this 6 times to trigger rate limit
for i in {1..6}; do
  curl -X POST http://localhost:5000/api/users/login/ \
    -H "Content-Type: application/json" \
    -d '{
      "username_or_email": "test@example.com",
      "password": "WrongPassword"
    }'
  sleep 1
done
```

## 🚨 Common Issues & Solutions

### Issue: JWT module not found
```bash
pip install djangorestframework-simplejwt PyJWT
```

### Issue: Token blacklist not working
Make sure you've run migrations:
```bash
python manage.py migrate
```

### Issue: Emails not sending
In development, check console output:
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

For production, configure SMTP:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### Issue: CORS errors from frontend
Update CORS settings in `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',
]
```

## 🎯 Frontend Integration

### React/JavaScript Example

```javascript
// Login
const login = async (email, password) => {
  const response = await fetch('http://localhost:5000/api/users/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username_or_email: email,
      password: password
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store tokens
    localStorage.setItem('access_token', data.token.access);
    localStorage.setItem('refresh_token', data.token.refresh);
    return data.user;
  } else {
    throw new Error(data.error);
  }
};

// Make authenticated request
const getProtectedData = async () => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:5000/api/users/verify-token/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
};

// Refresh token
const refreshToken = async () => {
  const refresh = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:5000/api/users/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
  }
};
```

## 📝 Summary

You now have a complete, production-ready authentication system with:

✅ JWT-based authentication
✅ Login with username or email
✅ Token refresh mechanism
✅ Secure logout with token blacklisting
✅ Password change functionality
✅ Password reset via email
✅ Rate limiting (5 attempts per 15 minutes)
✅ Security logging
✅ Input validation
✅ Error handling

The system is ready to use and can be easily integrated with your frontend application!
