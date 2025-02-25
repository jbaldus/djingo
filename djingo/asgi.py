# djingo/asgi.py
import os
import django
from django.core.asgi import get_asgi_application

# Set up Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djingo.settings')
django.setup()

# Now we can import our routing
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from bingo.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})