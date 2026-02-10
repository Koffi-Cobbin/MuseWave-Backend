# Production Deployment Guide - Authentication System

## 🚀 Production Checklist

### 1. Environment Variables

Create `.env` file with production values:

```bash
# Django
SECRET_KEY='your-super-secret-production-key-change-this'
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (PostgreSQL recommended)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=musewave_db
DB_USER=musewave_user
DB_PASSWORD=strong-database-password
DB_HOST=localhost
DB_PORT=5432

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=MuseWave <noreply@musewave.com>

# Frontend
FRONTEND_URL=https://yourdomain.com

# Redis (for caching and rate limiting)
REDIS_URL=redis://localhost:6379/0
```

### 2. Update Settings for Production

Add to `config/settings.py`:

```python
import os
from pathlib import Path

# Read from environment
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Email - Production SMTP
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

FRONTEND_URL = os.environ.get('FRONTEND_URL')

# Redis for caching (production)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Logging - Production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/musewave/auth.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/musewave/error.log',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'auth_views': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 3. Install Production Dependencies

```bash
pip install psycopg2-binary redis django-redis gunicorn
```

Update `requirements.txt`:
```
Django==5.0.1
djangorestframework==3.14.0
django-cors-headers==4.3.1
python-dotenv==1.0.0
djangorestframework-simplejwt==5.3.1
PyJWT==2.8.0
psycopg2-binary==2.9.9
redis==5.0.1
django-redis==5.4.0
gunicorn==21.2.0
```

### 4. Database Setup

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE musewave_db;
CREATE USER musewave_user WITH PASSWORD 'your-password';
ALTER ROLE musewave_user SET client_encoding TO 'utf8';
ALTER ROLE musewave_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE musewave_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE musewave_db TO musewave_user;
\q

# Run migrations
python manage.py migrate
```

### 5. Redis Setup

```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test Redis
redis-cli ping
# Should return: PONG
```

### 6. Email Configuration

#### Gmail Setup:
1. Enable 2-factor authentication on your Gmail account
2. Generate app-specific password:
   - Go to Google Account settings
   - Security → App passwords
   - Generate password for "Mail"
3. Use this password in EMAIL_HOST_PASSWORD

#### SendGrid Setup (Alternative):
```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'your-sendgrid-api-key'
```

### 7. Gunicorn Configuration

Create `gunicorn_config.py`:

```python
import multiprocessing

# Server socket
bind = '0.0.0.0:8000'
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '/var/log/musewave/gunicorn_access.log'
errorlog = '/var/log/musewave/gunicorn_error.log'
loglevel = 'info'

# Process naming
proc_name = 'musewave'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
```

Run with:
```bash
gunicorn config.wsgi:application -c gunicorn_config.py
```

### 8. Nginx Configuration

Create `/etc/nginx/sites-available/musewave`:

```nginx
upstream musewave_backend {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
    limit_req_status 429;

    # Static files
    location /static/ {
        alias /var/www/musewave/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/musewave/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints with rate limiting
    location /api/users/login/ {
        limit_req zone=login_limit burst=10 nodelay;
        proxy_pass http://musewave_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # All other API endpoints
    location /api/ {
        proxy_pass http://musewave_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Admin
    location /admin/ {
        proxy_pass http://musewave_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/musewave /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 10. Systemd Service

Create `/etc/systemd/system/musewave.service`:

```ini
[Unit]
Description=MuseWave Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/musewave
Environment="PATH=/var/www/musewave/venv/bin"
ExecStart=/var/www/musewave/venv/bin/gunicorn \
          --config /var/www/musewave/gunicorn_config.py \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl start musewave
sudo systemctl enable musewave
sudo systemctl status musewave
```

### 11. Monitoring & Security

#### Fail2Ban for Login Protection

Create `/etc/fail2ban/filter.d/musewave-auth.conf`:

```ini
[Definition]
failregex = Auth attempt - User: .*, Success: False, IP: <HOST>
ignoreregex =
```

Create `/etc/fail2ban/jail.d/musewave.conf`:

```ini
[musewave-auth]
enabled = true
filter = musewave-auth
logpath = /var/log/musewave/auth.log
maxretry = 5
findtime = 600
bantime = 3600
```

Restart fail2ban:
```bash
sudo systemctl restart fail2ban
```

#### Log Rotation

Create `/etc/logrotate.d/musewave`:

```
/var/log/musewave/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload musewave
    endscript
}
```

### 12. Final Security Checklist

- [ ] SECRET_KEY is unique and secure
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS configured correctly
- [ ] Database using PostgreSQL with strong password
- [ ] Redis secured with password (if exposed)
- [ ] Email using SMTP with app-specific password
- [ ] SSL certificate installed and auto-renewing
- [ ] Nginx configured with security headers
- [ ] Rate limiting enabled
- [ ] Fail2Ban configured
- [ ] Log rotation configured
- [ ] Regular backups scheduled
- [ ] Firewall configured (only 80, 443 open)
- [ ] Server updates automated

### 13. Backup Strategy

```bash
#!/bin/bash
# backup.sh - Run daily via cron

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/musewave"

# Database backup
pg_dump -U musewave_user musewave_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/musewave/media/

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup.sh
```

## 🎉 Deployment Complete!

Your authentication system is now production-ready with:

✅ PostgreSQL database
✅ Redis caching
✅ Email via SMTP
✅ SSL encryption
✅ Rate limiting
✅ Security headers
✅ Monitoring & logging
✅ Automated backups
✅ Fail2Ban protection

Monitor logs:
```bash
tail -f /var/log/musewave/auth.log
tail -f /var/log/musewave/error.log
```
