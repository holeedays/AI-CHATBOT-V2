import os 
import sys
import asyncio
from celery import Celery

# this is just a fix for django channels and playwright's chromium launcher, we have to implement it in
# the asgi.py file in our root and manage.py
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cb_site.settings')
app = Celery('cb_site')
app.config_from_object('django.conf:settings', namespace='CELERY') 
app.autodiscover_tasks() 