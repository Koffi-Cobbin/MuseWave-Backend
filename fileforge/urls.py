"""
fileforge/urls.py
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DriveFileViewSet, TaskStatusView

router = DefaultRouter()
router.register(r"files", DriveFileViewSet, basename="drivefile")

urlpatterns = [
    path("", include(router.urls)),
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="fileforge-task-status"),
]