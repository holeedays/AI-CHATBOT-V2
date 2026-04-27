"""
ASGI config for cb_site project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import cbot.websocket.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cb_site.settings')

# monitors whether request should go to an http-like request or a websocket request and routes it
application = ProtocolTypeRouter({
    # it's like wsgi (a traditional HTTP interface), but can handle multiple requests at once
    "http": get_asgi_application(),
    # our websocket routing
    "websocket": AuthMiddlewareStack(
        URLRouter(
            cbot.websocket.routing.websocket_urlpatterns #type: ignore
        )
    )
})
