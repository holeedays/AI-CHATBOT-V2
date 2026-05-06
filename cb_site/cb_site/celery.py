import os 
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cb_site.settings')
app = Celery('cb_site')
app.config_from_object('django.conf:settings', namespace='CELERY') #type: ignore
app.autodiscover_tasks() #type: ignore