from django.contrib import admin
from .models import DriveFile


@admin.register(DriveFile)
class DriveFileAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "resource_type", "resource_id", "size_mb", "created_at"]
    list_filter = ["category", "resource_type"]
    search_fields = ["name", "file_id", "resource_id"]
    readonly_fields = ["id", "file_id", "folder_id", "url", "created_at", "updated_at"]