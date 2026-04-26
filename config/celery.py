"""
musewave/celery.py

Celery application entrypoint.
Add this file to your Django project root (musewave/ package).
"""

import os
from config.celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "musewave.settings")

app = Celery("musewave")

# Read broker/backend from Django settings (CELERY_* prefix)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")