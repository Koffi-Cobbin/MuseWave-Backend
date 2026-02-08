from django.core.management.base import BaseCommand
from musewave.models import User, Track, Like, Follow, Play, Album
from django.utils import timezone
import random


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')

        # Create sample users
        users_data = [
            {
                'username': 'dj_beats',
                'email': 'djbeats@example.com',
                'password': 'hashed_password_1',
                'display_name': 'DJ Beats',
                'bio': 'Electronic music producer specializing in house and techno',
                'avatar_url': 'https://i.pravatar.cc/300?img=1',
            },
            {
                'username': 'indie_artist',
                'email': 'indie@example.com',
                'password': 'hashed_password_2',
                'display_name': 'Indie Artist',
                'bio': 'Singer-songwriter with a passion for acoustic music',
                'avatar_url': 'https://i.pravatar.cc/300?img=2',
            },
            {
                'username': 'hiphop_king',
                'email': 'hiphop@example.com',
                'password': 'hashed_password_3',
                'display_name': 'Hip Hop King',
                'bio': 'Rapper and producer from the streets',
                'avatar_url': 'https://i.pravatar.cc/300?img=3',
            },
        ]

        users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            users.append(user)
            if created:
                self.stdout.write(f'Created user: {user.username}')

        # Create sample tracks
        tracks_data = [
            {
                'user': users[0],
                'title': 'Summer Nights',
                'artist': 'DJ Beats',
                'artist_slug': 'dj-beats',
                'genre': 'Electronic',
                'mood': 'Happy',
                'tags': ['summer', 'dance', 'upbeat'],
                'audio_url': 'https://example.com/tracks/summer-nights.mp3',
                'audio_file_size': 5242880,
                'audio_duration': 240.5,
                'audio_format': 'mp3',
                'published': True,
                'bpm': 128,
                'key': 'Am',
            },
            {
                'user': users[0],
                'title': 'Midnight Drive',
                'artist': 'DJ Beats',
                'artist_slug': 'dj-beats',
                'genre': 'Electronic',
                'mood': 'Chill',
                'tags': ['night', 'smooth', 'driving'],
                'audio_url': 'https://example.com/tracks/midnight-drive.mp3',
                'audio_file_size': 4800000,
                'audio_duration': 210.0,
                'audio_format': 'mp3',
                'published': True,
                'bpm': 110,
                'key': 'Dm',
            },
            {
                'user': users[1],
                'title': 'Coffee Shop Memories',
                'artist': 'Indie Artist',
                'artist_slug': 'indie-artist',
                'genre': 'Indie',
                'mood': 'Chill',
                'tags': ['acoustic', 'calm', 'coffee'],
                'audio_url': 'https://example.com/tracks/coffee-shop.mp3',
                'audio_file_size': 4194304,
                'audio_duration': 180.3,
                'audio_format': 'mp3',
                'published': True,
                'bpm': 90,
                'key': 'C',
            },
            {
                'user': users[2],
                'title': 'Street Dreams',
                'artist': 'Hip Hop King',
                'artist_slug': 'hiphop-king',
                'genre': 'Hip Hop',
                'mood': 'Energetic',
                'tags': ['rap', 'beats', 'urban'],
                'audio_url': 'https://example.com/tracks/street-dreams.mp3',
                'audio_file_size': 6291456,
                'audio_duration': 195.0,
                'audio_format': 'mp3',
                'published': True,
                'bpm': 95,
                'key': 'Dm',
            },
        ]

        tracks = []
        for track_data in tracks_data:
            track, created = Track.objects.get_or_create(
                title=track_data['title'],
                user=track_data['user'],
                defaults=track_data
            )
            tracks.append(track)
            if created:
                self.stdout.write(f'Created track: {track.title}')

        # Create sample albums
        albums_data = [
            {
                'user': users[0],
                'title': 'Electronic Dreams',
                'artist': 'DJ Beats',
                'genre': 'Electronic',
                'description': 'A collection of late-night electronic vibes',
                'release_date': timezone.now(),
                'published': True,
            },
        ]

        albums = []
        for album_data in albums_data:
            album, created = Album.objects.get_or_create(
                title=album_data['title'],
                user=album_data['user'],
                defaults=album_data
            )
            albums.append(album)
            if created:
                self.stdout.write(f'Created album: {album.title}')
                
                # Associate some tracks with this album
                user_tracks = [t for t in tracks if t.user == users[0]][:2]
                for track in user_tracks:
                    track.album = album
                    track.save()
                    self.stdout.write(f'  Added track "{track.title}" to album')

        # Create some likes
        for user in users:
            for track in random.sample(tracks, min(2, len(tracks))):
                like, created = Like.objects.get_or_create(
                    user=user,
                    track=track
                )
                if created:
                    track.likes += 1
                    track.save()

        # Create some follows
        for i, user in enumerate(users):
            for other_user in users[i+1:]:
                Follow.objects.get_or_create(
                    follower=user,
                    following=other_user
                )

        # Create some plays
        for track in tracks:
            for _ in range(random.randint(10, 50)):
                user = random.choice(users)
                Play.objects.create(
                    user=user,
                    track=track,
                    duration=random.uniform(30, track.audio_duration),
                    completed=random.choice([True, False])
                )
                track.plays += 1
            track.save()

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
