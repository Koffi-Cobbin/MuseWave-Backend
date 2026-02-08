# Album Feature - Migration and Usage Guide

## 🎵 What's New

Version 1.1.0 adds complete album functionality to organize tracks into collections.

## ✨ New Features

### 1. Album Model
Albums can group multiple tracks together with:
- Title and artist information
- Genre and description
- Cover artwork (URL or gradient)
- Release date
- Published status

### 2. Track-Album Relationship
- Tracks can optionally belong to an album
- Albums can contain multiple tracks
- Deleting an album doesn't delete tracks

### 3. New API Endpoints
- Create albums with track associations
- List user's albums
- Get album details with all tracks
- Update and delete albums

## 🚀 Getting Started

### Step 1: Run Database Migrations

After updating to version 1.1.0, run migrations to add the Album table:

```bash
cd django-music-backend
source venv/bin/activate  # If not already activated
python manage.py makemigrations
python manage.py migrate
```

This will:
- Create the `albums` table
- Add `album_id` column to `tracks` table
- Set up proper relationships and indexes

### Step 2: (Optional) Load Sample Data

To see albums in action with sample data:

```bash
python manage.py seed_data
```

This creates:
- Sample users
- Sample tracks  
- A sample album with associated tracks

## 📖 API Usage Examples

### Create an Album

```bash
POST /musewave/albums
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Summer Hits 2024",
  "artist": "DJ Beats",
  "genre": "Electronic",
  "description": "The best summer electronic tracks",
  "release_date": "2024-06-01T00:00:00Z",
  "published": true,
  "track_ids": [
    "track-uuid-1",
    "track-uuid-2",
    "track-uuid-3"
  ]
}
```

**Response:**
```json
{
  "id": "album-uuid",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Summer Hits 2024",
  "artist": "DJ Beats",
  "genre": "Electronic",
  "description": "The best summer electronic tracks",
  "release_date": "2024-06-01T00:00:00Z",
  "published": true,
  "track_count": 3,
  "created_at": "2024-02-08T10:00:00Z",
  "updated_at": "2024-02-08T10:00:00Z"
}
```

### Get User's Albums

```bash
GET /musewave/users/550e8400-e29b-41d4-a716-446655440000/albums
```

**Response:**
```json
[
  {
    "id": "album-uuid-1",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Summer Hits 2024",
    "artist": "DJ Beats",
    "genre": "Electronic",
    "track_count": 3,
    "published": true,
    "created_at": "2024-02-08T10:00:00Z"
  },
  {
    "id": "album-uuid-2",
    "title": "Winter Collection",
    "track_count": 5,
    "published": false,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

### Get Album with All Tracks

```bash
GET /musewave/albums/album-uuid-1
```

**Response:**
```json
{
  "id": "album-uuid-1",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Summer Hits 2024",
  "artist": "DJ Beats",
  "genre": "Electronic",
  "description": "The best summer electronic tracks",
  "track_count": 3,
  "published": true,
  "tracks": [
    {
      "id": "track-uuid-1",
      "title": "Summer Nights",
      "artist": "DJ Beats",
      "album_id": "album-uuid-1",
      "duration": 240.5,
      "genre": "Electronic"
    },
    {
      "id": "track-uuid-2",
      "title": "Beach Party",
      "album_id": "album-uuid-1",
      "duration": 180.0
    }
  ]
}
```

### Update Album

```bash
PATCH /musewave/albums/album-uuid-1/update
Content-Type: application/json

{
  "title": "Ultimate Summer Hits 2024",
  "description": "Updated description",
  "published": true
}
```

### Delete Album

```bash
DELETE /musewave/albums/album-uuid-1/delete
```

**Important:** Deleting an album:
- Removes the album record
- Removes track associations (sets `album_id` to null on tracks)
- Does NOT delete the tracks themselves

## 🔧 Frontend Integration

Based on the `album-create.tsx` component structure:

### 1. Fetch User's Published Tracks

```javascript
const response = await fetch(`/musewave/tracks?userId=${userId}&published=true`);
const tracks = await response.json();
```

### 2. Allow User to Select Tracks

Display tracks with checkboxes for selection

### 3. Submit Album Creation

```javascript
const albumData = {
  user_id: userId,
  title: "My Album",
  artist: artistName,
  genre: "Electronic",
  description: "Album description",
  release_date: new Date().toISOString(),
  published: true,
  track_ids: selectedTrackIds  // Array of track UUIDs
};

const response = await fetch('/musewave/albums', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(albumData)
});

const album = await response.json();
```

### 4. Display Albums

```javascript
// Get user's albums
const response = await fetch(`/musewave/users/${userId}/albums`);
const albums = await response.json();

// Get specific album with tracks
const albumResponse = await fetch(`/musewave/albums/${albumId}`);
const albumWithTracks = await albumResponse.json();
```

## 📊 Database Schema Changes

### New Table: albums
```sql
CREATE TABLE albums (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    artist VARCHAR(200) NOT NULL,
    description TEXT,
    cover_url TEXT,
    cover_gradient VARCHAR(255),
    release_date TIMESTAMP NOT NULL,
    genre VARCHAR(50) NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Updated Table: tracks
```sql
ALTER TABLE tracks
ADD COLUMN album_id UUID REFERENCES albums(id) ON DELETE SET NULL;
```

## 🎯 Use Cases

### 1. Organize Singles into an Album
```python
# Artist has 5 published singles
# Create an album and group them
album = create_album({
    "title": "Best of 2024",
    "track_ids": [single1_id, single2_id, single3_id]
})
```

### 2. Release a Full Album
```python
# Upload all tracks first
track1 = create_track({...})
track2 = create_track({...})
track3 = create_track({...})

# Then create album
album = create_album({
    "title": "Full Album",
    "track_ids": [track1.id, track2.id, track3.id],
    "published": True
})
```

### 3. Manage Track Collections
```python
# Remove track from album
update_track(track_id, {"album_id": None})

# Add track to different album
update_track(track_id, {"album_id": new_album_id})

# Delete album (tracks remain)
delete_album(album_id)
# Tracks now have album_id = None
```

## ⚠️ Important Notes

1. **Optional Relationship:** Tracks don't need to belong to an album
2. **No Cascade Delete:** Deleting an album doesn't delete tracks
3. **Track Ownership:** Only tracks owned by the album's user can be associated
4. **Published Status:** Albums and tracks have independent published status

## 🔍 Backward Compatibility

All existing API endpoints continue to work:
- Track endpoints now include `album_id` field (nullable)
- Existing tracks have `album_id = null`
- No changes required for existing frontend code

## 📈 Next Steps

After migration:

1. **Test Album Creation:** Create a sample album via API
2. **Verify Relationships:** Check track-album associations
3. **Update Frontend:** Add album UI components
4. **Test Edge Cases:** Delete albums, remove associations, etc.

## 🆘 Troubleshooting

### Migration Issues

**Problem:** Migration fails
```bash
# Reset migrations if needed
python manage.py migrate api zero
python manage.py makemigrations
python manage.py migrate
```

**Problem:** Existing data conflicts
- Albums are a new feature, no existing data conflicts
- All tracks start with `album_id = null`

### API Issues

**Problem:** Cannot create album
- Verify user exists
- Check track IDs are valid and belong to the user
- Ensure all required fields are provided

**Problem:** Tracks not associated with album
- Verify track IDs in request body
- Check tracks belong to the same user as album
- Ensure tracks exist before creating album

## 📝 Summary

The album feature is now ready to use! You can:
- ✅ Create albums with multiple tracks
- ✅ List albums by user
- ✅ View album details with all tracks
- ✅ Update album information
- ✅ Delete albums (tracks remain)
- ✅ Manage track-album associations

All changes are backwards compatible and ready for production use.
