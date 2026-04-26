import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "constructor_express.settings")

app = Celery("constructor_express")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
