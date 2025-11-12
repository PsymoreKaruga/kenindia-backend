# backend/kenindia_core/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kenindia_core.settings')

app = Celery('kenindia')
app.config_from_object('django.conf:settings', namespace='CELERY')

# THIS WILL NOW USE REDIS_URL FROM ENV OR DOCKER
app.conf.broker_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
app.conf.result_backend = os.environ.get('REDIS_URL', 'redis://redis:6379/1').replace('/0', '/1')

app.autodiscover_tasks()