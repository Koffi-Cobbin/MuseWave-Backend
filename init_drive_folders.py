"""
Management command: python manage.py init_drive_folders

Ensures MuseWave folder structure exists in the admin Google Drive.
Safe to run multiple times (idempotent).
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create/verify MuseWave folder structure in the admin Google Drive account."

    def handle(self, *args, **options):
        from fileforge.services.folder_manager import ensure_base_structure

        self.stdout.write("Verifying MuseWave Drive folder structure...")
        try:
            folder_ids = ensure_base_structure()
            self.stdout.write(self.style.SUCCESS("Folder structure OK:"))
            for label, fid in folder_ids.items():
                self.stdout.write(f"  {label:20s} → {fid}")
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Failed: {exc}"))
            raise SystemExit(1)