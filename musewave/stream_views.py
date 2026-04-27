"""
music/views_stream.py

Wire GET /api/tracks/{id}/stream/ into the music app using FileForge's proxy streamer.
Include this in music/urls.py.
"""

import re

from django.http import StreamingHttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from fileforge.services.google_drive import get_file as drive_get_meta, stream_file_chunks


class TrackStreamView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, track_id):
        from musewave.models import Track  # local import to avoid circular

        try:
            track = Track.objects.select_related("audio_file").get(pk=track_id)
        except Track.DoesNotExist:
            return Response({"detail": "Track not found."}, status=status.HTTP_404_NOT_FOUND)

        if not track.audio_file:
            return Response({"detail": "No audio file attached."}, status=status.HTTP_404_NOT_FOUND)

        drive_file = track.audio_file
        file_id = drive_file.file_id

        meta = drive_get_meta(file_id)
        total_size = int(meta.get("size", 0))
        mime_type = drive_file.file_type or "audio/mpeg"

        range_header = request.META.get("HTTP_RANGE", "")
        start, end = 0, total_size - 1
        http_status = 200

        if range_header:
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else total_size - 1
                end = min(end, total_size - 1)
                http_status = 206

        content_length = end - start + 1

        def audio_iterator():
            yield from stream_file_chunks(file_id, start=start, end=end)

        response = StreamingHttpResponse(audio_iterator(), status=http_status, content_type=mime_type)
        response["Content-Length"] = content_length
        response["Accept-Ranges"] = "bytes"
        response["Content-Disposition"] = f'inline; filename="{drive_file.name}"'
        if http_status == 206:
            response["Content-Range"] = f"bytes {start}-{end}/{total_size}"

        return response