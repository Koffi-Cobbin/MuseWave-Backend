# MuseWave Authentication System - Complete Package

## 📦 What's Included

This package provides a complete, production-ready authentication system for your Django MuseWave backend.

### Core Files (7 files)

1. **auth_serializers.py** - Data validation and serialization
   - LoginSerializer
   - UserDetailSerializer
   - ChangePasswordSerializer
   - PasswordResetRequestSerializer
   - PasswordResetConfirmSerializer

2. **auth_views.py** - API endpoint handlers
   - login_view
   - logout_view
   - token_refresh_view
   - verify_token_view
   - change_password_view
   - password_reset_request_view
   - password_reset_confirm_view

3. **auth_urls.py** - URL routing patterns
   - All authentication endpoint mappings

4. **settings_additions.py** - Django settings configuration
   - JWT configuration
   - Email settings
   - Caching setup
   - Logging configuration

5. **requirements_auth.txt** - Python dependencies
   - djangorestframework-simplejwt
   - PyJWT

6. **test_auth_api.sh** - Comprehensive API testing script
   - Tests all endpoints
   - Rate limiting tests
   - Error case tests

7. **AUTH_README.md** - Quick reference guide
   - API documentation
   - Quick start guide
   - Common issues

### Documentation Files (2 files)

8. **AUTH_INSTALLATION_GUIDE.md** - Step-by-step installation
   - Detailed setup instructions
   - Configuration examples
   - Frontend integration guide

9. **PRODUCTION_DEPLOYMENT.md** - Production deployment guide
   - PostgreSQL setup
   - Redis configuration
   - Nginx configuration
   - SSL setup
   - Monitoring and security

## 🎯 Features Overview

### Authentication
✅ Login with username or email
✅ JWT token generation
✅ Token refresh mechanism
✅ Secure logout with token blacklisting
✅ Token verification endpoint
✅ Last login timestamp tracking

### Password Management
✅ Change password (requires old password)
✅ Password reset request (email-based)
✅ Password reset confirmation (token-based)
✅ Password strength validation
✅ Re-authentication after password change

### Security
✅ Rate limiting (5 attempts per 15 minutes)
✅ Account lockout after failed attempts
✅ Generic error messages (prevents user enumeration)
✅ IP address tracking
✅ User agent logging
✅ Authentication attempt logging
✅ Token blacklist on logout
✅ Secure password hashing

## 🚀 Quick Implementation Guide

### Step 1: Copy Files

```bash
# Copy to your musewave app directory
cp auth_serializers.py /path/to/musewave/
cp auth_views.py /path/to/musewave/
```

### Step 2: Install Dependencies

```bash
pip install djangorestframework-simplejwt==5.3.1 PyJWT==2.8.0
```

### Step 3: Update Settings

Add to `config/settings.py`:

```python
INSTALLED_APPS = [
    # ... existing
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### Step 4: Update URLs

Add to `musewave/urls.py`:

```python
from . import auth_views

urlpatterns = [
    path('users/login/', auth_views.login_view),
    path('users/logout/', auth_views.logout_view),
    path('users/refresh/', auth_views.token_refresh_view),
    path('users/verify-token/', auth_views.verify_token_view),
    path('users/password/change/', auth_views.change_password_view),
    path('users/password/reset/', auth_views.password_reset_request_view),
    path('users/password/reset/confirm/', auth_views.password_reset_confirm_view),
    # ... existing URLs
]
```

### Step 5: Run Migrations

```bash
python manage.py migrate
```

### Step 6: Test

```bash
chmod +x test_auth_api.sh
./test_auth_api.sh
```

## 📖 API Endpoints Summary

### Authentication Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/users/login/` | POST | No | User login |
| `/api/users/logout/` | POST | Yes | User logout |
| `/api/users/refresh/` | POST | No | Refresh access token |
| `/api/users/verify-token/` | GET | Yes | Verify token validity |

### Password Management Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/users/password/change/` | POST | Yes | Change password |
| `/api/users/password/reset/` | POST | No | Request password reset |
| `/api/users/password/reset/confirm/` | POST | No | Confirm password reset |

## 🔧 Configuration Options

### Rate Limiting

Default: 5 attempts per 15 minutes

```python
# auth_views.py
def check_rate_limit(identifier, max_attempts=5, window_minutes=15):
```

### Token Lifetime

```python
# settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 1 hour
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # 7 days
}
```

### Email Backend

Development (console):
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Production (SMTP):
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## 🧪 Testing Examples

### Test Login (curl)

```bash
curl -X POST http://localhost:5000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "test@example.com",
    "password": "password123"
  }'
```

### Test Protected Endpoint (curl)

```bash
curl -X GET http://localhost:5000/api/users/verify-token/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Frontend Integration (JavaScript)

```javascript
// Login
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

// Make authenticated request
const token = localStorage.getItem('access_token');
const response = await fetch('/api/protected-endpoint/', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## 📊 Security Features Breakdown

### 1. Rate Limiting
- Prevents brute force attacks
- IP + username combination tracking
- Configurable limits and windows
- Automatic reset on successful login

### 2. Token Management
- Access tokens expire after 1 hour
- Refresh tokens expire after 7 days
- Automatic token rotation on refresh
- Token blacklisting on logout

### 3. Password Security
- Minimum 8 characters
- Cannot be common passwords
- Cannot be too similar to user info
- Cannot be entirely numeric
- Secure hashing with Django's defaults

### 4. Logging
- All authentication attempts logged
- IP address and user agent tracked
- Success/failure tracking
- Separate log files for errors

### 5. Error Messages
- Generic messages to prevent enumeration
- Don't reveal if username/email exists
- Consistent error format

## 🚨 Important Notes

### Development vs Production

**Development:**
- Email to console
- In-memory caching
- Debug logging enabled
- CORS allow all origins

**Production:**
- SMTP email delivery
- Redis caching
- Error-level logging
- Specific CORS origins
- SSL/TLS required
- Security headers enabled

### Password Reset Flow

1. User requests reset with email
2. System generates token and UID
3. Email sent with reset link
4. User clicks link (frontend)
5. Frontend extracts UID and token
6. User enters new password
7. Frontend sends to confirm endpoint
8. Password updated, user can login

### Token Refresh Strategy

- Use access token for requests
- When access token expires (401)
- Use refresh token to get new access token
- Update stored access token
- Retry original request

## 📝 Checklist

### Installation
- [ ] Copy auth_serializers.py to musewave/
- [ ] Copy auth_views.py to musewave/
- [ ] Install dependencies
- [ ] Update settings.py
- [ ] Update urls.py
- [ ] Run migrations
- [ ] Test with curl commands

### Production Deployment
- [ ] Configure PostgreSQL
- [ ] Configure Redis
- [ ] Set up SMTP email
- [ ] Configure Nginx
- [ ] Install SSL certificate
- [ ] Set up logging
- [ ] Configure backups
- [ ] Enable monitoring

### Security
- [ ] Change SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable rate limiting
- [ ] Configure Fail2Ban
- [ ] Set up log rotation
- [ ] Enable security headers

## 🎉 You're Ready!

With this authentication system, you have:

✅ Complete JWT authentication
✅ Secure password management
✅ Rate limiting protection
✅ Production-ready security
✅ Comprehensive logging
✅ Email integration
✅ Frontend-ready APIs

## 📚 Documentation Reference

1. **AUTH_README.md** - Quick reference and API docs
2. **AUTH_INSTALLATION_GUIDE.md** - Detailed setup guide
3. **PRODUCTION_DEPLOYMENT.md** - Production deployment guide
4. **test_auth_api.sh** - Automated testing script

## 🤝 Support

If you encounter issues:

1. Check the documentation
2. Review log files
3. Test with provided curl commands
4. Verify settings configuration

Common logs locations:
- Development: Console output
- Production: `/var/log/musewave/auth.log`

## 💡 Next Steps

After installation:

1. Create a test user
2. Test all endpoints with curl
3. Integrate with your frontend
4. Configure email for production
5. Set up monitoring
6. Deploy to production

Happy coding! 🚀
