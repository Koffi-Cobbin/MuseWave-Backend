# Changelog

## Version 1.1.0 - Album Feature Addition (2024-02-08)

### 🎵 New Features

#### Album Management
- Added complete album CRUD functionality
- Albums can group multiple tracks together
- Track-to-album associations with optional relationships

#### New Model: Album
- **Fields:**
  - id (UUID) - Primary key
  - user (ForeignKey) - Album owner
  - title - Album name
  - artist - Artist name
  - description - Album description
  - cover_url - Album cover image
  - cover_gradient - Gradient for default covers
  - release_date - Album release date
  - genre - Music genre
  - published - Publication status
  - created_at - Creation timestamp
  - updated_at - Last update timestamp

#### New API Endpoints
- `GET /musewave/users/<user_id>/albums` - Get all albums for a user
- `GET /musewave/albums/<id>` - Get album by ID (includes all tracks)
- `POST /musewave/albums` - Create new album with track associations
- `PATCH /musewave/albums/<id>/update` - Update album details
- `DELETE /musewave/albums/<id>/delete` - Delete album (tracks remain)

#### Track Updates
- Added `album` field to Track model (ForeignKey, nullable)
- Tracks can now belong to an album (optional)
- Album association preserved in track serialization
- Track serializer now includes `album_id` field

### 📝 Updated Components

#### Models (`musewave/models.py`)
- Added Album model before Track model
- Updated Track model with album foreign key
- Album model has proper relationships and metadata

#### Serializers (`musewave/serializers.py`)
- Added `AlbumSerializer` for reading albums
- Added `CreateAlbumSerializer` for creating albums with track associations
- Updated `TrackSerializer` to include `album_id` field
- Album serializer includes `track_count` computed field

#### Views (`musewave/views.py`)
- Added `get_user_albums()` - List albums for a user
- Added `get_album()` - Get album with all tracks
- Added `create_album()` - Create album and associate tracks
- Added `update_album()` - Update album details
- Added `delete_album()` - Delete album (removes track associations)

#### URLs (`musewave/urls.py`)
- Added `/musewave/users/<user_id>/albums` route
- Added `/musewave/albums` route for creation
- Added `/musewave/albums/<id>` route for retrieval
- Added `/musewave/albums/<id>/update` route
- Added `/musewave/albums/<id>/delete` route

#### Admin (`musewave/admin.py`)
- Registered Album model in Django admin
- Added AlbumAdmin with list display and filters
- Updated TrackAdmin to show album association

#### Sample Data (`seed_data.py`)
- Added sample album creation
- Added track-to-album associations in seed data
- More tracks added for better album demonstration

### 📚 Documentation Updates
- Updated README.md with album endpoints
- Added album creation example
- Updated database models section
- Updated PROJECT_SUMMARY.md
- Added this CHANGELOG

### 🔧 Technical Details

#### Database Changes
- New `albums` table created
- Track table has new `album_id` column (nullable foreign key)
- Proper indexes and relationships configured
- Migration files will be generated on first run

#### API Behavior
- When creating an album with `track_ids`, tracks are automatically associated
- Deleting an album removes the association but keeps the tracks
- Updating tracks can change or remove album association
- Album retrieval includes all associated tracks

#### Frontend Integration
Based on the provided `album-create.tsx` component:
- Frontend can list user's published tracks
- User can select multiple tracks for an album
- Form includes: title, description, genre, artist
- Track selection uses checkbox interface
- Creates album with associated track IDs

### 🔄 Migration Notes

If upgrading from previous version:

1. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Update any existing API calls:**
   - Track objects now include `album_id` field (may be null)
   - New album endpoints available

3. **Optional: Seed new data:**
   ```bash
   python manage.py seed_data
   ```

### 🎯 Example Usage

**Create an Album:**
```bash
POST /musewave/albums
{
  "user_id": "user-uuid",
  "title": "My First Album",
  "artist": "Artist Name",
  "genre": "Electronic",
  "description": "Collection of my best tracks",
  "release_date": "2024-06-01T00:00:00Z",
  "published": true,
  "track_ids": ["track-1-uuid", "track-2-uuid"]
}
```

**Get Album with Tracks:**
```bash
GET /musewave/albums/<album-uuid>
```

**List User's Albums:**
```bash
GET /musewave/users/<user-uuid>/albums
```

### 🐛 Bug Fixes
- None (new feature)

### ⚠️ Breaking Changes
- None - all changes are backwards compatible
- Existing track endpoints continue to work
- `album_id` in track responses will be `null` for tracks without albums

### 📊 Statistics
- **New Models:** 1 (Album)
- **Updated Models:** 1 (Track)
- **New Endpoints:** 5
- **New Serializers:** 2
- **Lines of Code Added:** ~200+

---

## Version 1.0.0 - Initial Release (2024-02-04)

Initial Django backend implementation with:
- User management
- Track management  
- Social features (likes, follows, plays)
- Analytics and statistics
- Search functionality
- Admin interface
- Complete API parity with Express backend
