from django.apps import AppConfig


class FileforgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fileforge"
    verbose_name = "FileForge"

    def ready(self):
        # Ensure folder structure is validated at startup (non-blocking)
        pass