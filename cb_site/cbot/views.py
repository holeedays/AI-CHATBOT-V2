from django.shortcuts import render
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse

from .services.data_caching import DataCache
import asyncio
import time

# Create your views here.
def home_pg(request: HttpRequest) -> HttpResponse:

    # since cookies only get written during a request/response cycle (not websocket it seems...)
    # we'll create a new session over here versus in our websocket consumers.py
    dc = DataCache(request.session) #type: ignore

    dc.generate_cookie()
    dc.generate_chat_session()

    return render(request, "cbot/index.html")