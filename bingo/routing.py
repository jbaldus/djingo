# bingo/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path(r'ws/game/<int:player_id>/', consumers.BingoGameConsumer.as_asgi()),
    # path(r'ws/event/', consumers.EventConsumer.as_asgi()),

]