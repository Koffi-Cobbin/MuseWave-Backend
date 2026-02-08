# Migration Guide: Express/TypeScript to Django

This document helps you understand the differences between the original Express/TypeScript backend and this Django implementation.

## Architecture Comparison

### Express Backend
```
server/
├── index.ts          # Express app setup
├── routes.ts         # API route definitions
├── storage.ts        # JSON file-based database
└── static.ts         # Static file serving
```

### Django Backend
```
django-music-backend/
├── manage.py                  # Django CLI tool
├── config/             # Project configuration
│   ├── settings.py           # All settings
│   ├── urls.py               # Root URL routing
│   └── wsgi.py              # WSGI application
└── musewave/                       # Main app
    ├── models.py             # Database models (ORM)
    ├── views.py              # API view functions
    ├── serializers.py        # Data serialization
    ├── urls.py               # API URL routing
    ├── admin.py              # Admin interface config
    ├── middleware.py         # Request logging
    └── management/           # Custom commands
        └── commands/
            └── seed_data.py  # Database seeding
```

## Key Differences

### 1. Data Storage

**Express (JSON Files)**
```typescript
// Read/write to JSON files
private readFile<T>(filePath: string): T {
  const data = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(data);
}
```

**Django (Database with ORM)**
```python
# Use Django ORM
users = User.objects.filter(verified=True)
track = Track.objects.get(id=track_id)
```

**Advantages of Django ORM:**
- Automatic indexing and query optimization
- Type safety at database level
- Built-in migrations
- Support for complex queries
- Transaction management
- Easy to switch databases (SQLite → PostgreSQL)

### 2. API Endpoints

Both backends expose identical REST endpoints, but implementation differs:

**Express**
```typescript
app.get("/musewave/users/:id", asyncHandler(async (req: any, res: any) => {
  const user = await jsonDb.getUser(req.params.id);
  if (!user) {
    return res.status(404).json({ error: "User not found" });
  }
  const { password, ...safeUser } = user;
  res.json(safeUser);
}));
```

**Django**
```python
@api_view(['GET'])
def get_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    serializer = UserSerializer(user)
    return Response(serializer.data)
```

### 3. Data Validation

**Express (Zod)**
```typescript
const createUserSchema = z.object({
  username: z.string().min(3).max(30),
  email: z.string().email(),
  // ...
});
```

**Django (DRF Serializers)**
```python
class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', ...]
        extra_kwargs = {
            'username': {'min_length': 3, 'max_length': 30},
        }
```

### 4. Middleware & Logging

**Express**
```typescript
app.use((req, res, next) => {
  const start = Date.now();
  res.on("finish", () => {
    const duration = Date.now() - start;
    log(`${req.method} ${path} ${res.statusCode} in ${duration}ms`);
  });
  next();
});
```

**Django**
```python
class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()
    
    def process_response(self, request, response):
        duration = int((time.time() - request._start_time) * 1000)
        print(f"{request.method} {request.path} {response.status_code} in {duration}ms")
        return response
```

## Performance Comparison

### Query Performance

**Express (JSON Files)**
- Simple filtering: O(n) - must scan entire file
- Sorting: O(n log n) - load all, then sort
- No indexes - every query is a full scan

**Django (SQLite/PostgreSQL)**
- Indexed queries: O(log n)
- Database-level sorting and filtering
- Connection pooling
- Query caching

### Example: Finding tracks by genre

**Express**
```typescript
// Loads ALL tracks into memory, then filters
const tracks = this.readFile<Track[]>(DB_FILES.tracks);
return tracks.filter((t) => t.genre === genre);
```

**Django**
```python
# Database only returns matching rows
tracks = Track.objects.filter(genre=genre)
```

## Feature Additions in Django

### 1. Admin Interface
Django includes a built-in admin panel at `/admin/`:
- Visual interface for all models
- CRUD operations without code
- User authentication
- Customizable interface

### 2. Database Migrations
```bash
python manage.py makemigrations  # Create migration files
python manage.py migrate         # Apply to database
```

### 3. Management Commands
```bash
python manage.py seed_data       # Custom command to seed data
python manage.py createsuperuser # Built-in commands
```

### 4. Better Error Handling
- Automatic HTTP status codes
- Validation error details
- Stack trace in development
- Custom exception handlers

## API Endpoint Mapping

All endpoints are identical:

| Endpoint | Express | Django |
|----------|---------|--------|
| Create User | POST `/musewave/users` | POST `/musewave/users` |
| Get User | GET `/musewave/users/:id` | GET `/musewave/users/<id>` |
| List Tracks | GET `/musewave/tracks?genre=...` | GET `/musewave/tracks?genre=...` |
| Like Track | POST `/musewave/tracks/:id/like` | POST `/musewave/tracks/<id>/like` |
| Search | GET `/musewave/search?q=...` | GET `/musewave/search?q=...` |

## Environment Variables

**Express (.env)**
```
PORT=5000
NODE_ENV=production
```

**Django (.env)**
```
SECRET_KEY=your-secret-key
DEBUG=True
PORT=5000
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Running the Server

**Express**
```bash
npm install
npm start
```

**Django**
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:5000
```

Or use the quick start script:
```bash
chmod +x quickstart.sh
./quickstart.sh
```

## Testing

**Express**
Would need to set up Jest or Mocha

**Django**
Built-in test framework:
```python
from django.test import TestCase

class UserTestCase(TestCase):
    def test_create_user(self):
        response = self.client.post('/musewave/users', {...})
        self.assertEqual(response.status_code, 201)
```

Run tests:
```bash
python manage.py test
```

## Deployment

### Express (Node.js)
- Requires Node.js runtime
- Process manager (PM2)
- Reverse proxy (Nginx)

### Django
- Multiple options:
  - Gunicorn (WSGI server)
  - uWSGI
  - Daphne (ASGI)
- Same reverse proxy setup
- Better process management

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:5000 --workers 4
```

## Database Migration

If you have existing JSON data from Express:

1. Export JSON data from Express backend
2. Create a Django management command to import:

```python
# musewave/management/commands/import_json.py
from django.core.management.base import BaseCommand
import json

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open('db-data/users.json') as f:
            users = json.load(f)
            for user_data in users:
                User.objects.create(**user_data)
```

3. Run: `python manage.py import_json`

## Advantages of Django Backend

1. **Performance**: Database queries are much faster than JSON file operations
2. **Scalability**: Easy to scale with database replication
3. **Admin Interface**: Built-in UI for data management
4. **Security**: Built-in protection against SQL injection, CSRF, XSS
5. **Ecosystem**: Extensive library of packages
6. **Testing**: Built-in test framework
7. **Migrations**: Version-controlled database changes
8. **Production-Ready**: Battle-tested in production environments

## When to Use Each

**Use Express/JSON if:**
- Prototyping/MVP
- Very simple data requirements
- Team is JavaScript-only
- Need real-time features (Socket.io)

**Use Django if:**
- Production application
- Complex data relationships
- Need admin interface
- Scaling to many users
- Team knows Python
- Want built-in security features

## Conclusion

Both backends provide the same API interface, making them interchangeable from a frontend perspective. Django offers better performance, scalability, and production features, while Express with JSON files is simpler for prototyping.

Choose based on your project's needs and your team's expertise.
