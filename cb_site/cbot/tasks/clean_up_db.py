from celery import shared_task
from django.contrib.sessions.models import Session

from .. import models as mdls
from ..services.data_caching import DataCache

@shared_task
def clean_up_old_cookies():
    dc = DataCache()
    # retrieve all cookies
    all_cookies: list[mdls.CookieSession] = dc.get_cookies()
    # create hash mapping of all ids for fast checking 
    all_session_ids: set[str] = set(Session.objects.values_list('session_key', flat=True))
    for cookie in all_cookies:
        if (not cookie.id in all_session_ids):
            dc.remove_cached_cookies(cookie)

    print("All unused cookies have been removed")