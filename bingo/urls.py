# bingo/urls.py
from django.urls import path, include
from rest_framework import routers
from . import views
from . import api_views

# DRF router for API endpoints
# router = routers.DefaultRouter()
# router.register(r'boards', api_views.BingoBoardViewSet, basename='board')
# router.register(r'games', api_views.BingoGameViewSet, basename='game')

urlpatterns = [
    # Main routes
    path('', views.home, name='home'),
    path('play/<str:code>/', views.join_game, name='join_game'),
    path('game/<int:player_id>/', views.play_game, name='play_game'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/game/<int:player_id>/clear/', views.clear_board, name='clear_board'),
    
    # API routes
    # path('api/', include(router.urls)),
]