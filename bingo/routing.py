# bingo/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path(r'ws/play/<int:player_id>/', consumers.BingoGameConsumer.as_asgi()),
    path(r'ws/spectate/<str:game_code>/', consumers.SpectatorConsumer.as_asgi()),
    # path(r'ws/event/', consumers.EventConsumer.as_asgi()),
]