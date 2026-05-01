from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class TrackStreamView(APIView):
    """
    Redirects the client to the track's audio_url for streaming.
    Audio files are expected to be externally hosted (CDN, S3, etc.).
    """
    permission_classes = [AllowAny]

    def get(self, request, track_id):
        from musewave.models import Track

        try:
            track = Track.objects.get(pk=track_id)
        except Track.DoesNotExist:
            return Response({"detail": "Track not found."}, status=status.HTTP_404_NOT_FOUND)

        if not track.audio_url:
            return Response({"detail": "No audio file attached."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"audio_url": track.audio_url})
