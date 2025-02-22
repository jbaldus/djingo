from django.urls import path
from . import views

urlpatterns = [
    path('join/<str:code>', views.join_game, name='join_game'),
    path('play/<int:player_id>', views.play_game, name='play_game'),
    path('play/<str:gamecode>/markposition', views.mark_position, name='mark_position'),
]
