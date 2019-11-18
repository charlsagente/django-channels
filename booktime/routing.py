from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from channels.http import AsgiHandler
import main.routing

application = ProtocolTypeRouter(
    {
        # (http->django views is added by default)
        'websocket': AuthMiddlewareStack(
            URLRouter(
                main.routing.websocket_urlpatterns
            )
        ),
        "http": URLRouter(
          main.routing.http_urlpatterns + [re_path(r"", AsgiHandler)]
        ),
    }
)
