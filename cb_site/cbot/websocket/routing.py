from django.urls import re_path
from . import consumers

websocket_urlpatterns = [ #type: ignore
    # normally the path is 'ws/chat/$', but the endpoint doesn't really matter so long as it'sconsistent with the frontend
    re_path(r'ws/response_stream/$', consumers.ChatConsumer.as_asgi()) #type: ignore
]