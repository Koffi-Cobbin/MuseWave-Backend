"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('musewave.urls')),
    path("api/fileforge/", include("fileforge.urls")),
    # path("api/tracks/<int:track_id>/stream/", TrackStreamView.as_view(), name="track-stream"),
]