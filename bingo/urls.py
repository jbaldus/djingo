# bingo/urls.py
from django.urls import path, include
from rest_framework import routers
from . import views
from . import api_views

# DRF router for API endpoints
router = routers.DefaultRouter()
router.register(r'boards', api_views.BingoBoardViewSet, basename='board')
router.register(r'games', api_views.BingoGameViewSet, basename='game')

handler404 = 'bingo.views.view_404'

urlpatterns = [
    # Main routes
    path('', views.home, name='home'),
    path('join/<str:code>/', views.join_game, name='join_game'),
    path('play/<int:player_id>/', views.play_game, name='play_game'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('play/<int:player_id>/clear/', views.clear_board, name='clear_board'),
    path('play/<int:player_id>/share', views.share_game, name='share_game'),

    path('review-suggestions/', views.review_suggestions, name='review_suggestions'),
    path('approve-item/<int:item_id>/', views.approve_item, name='approve_item'),
    path('deny-item/<int:item_id>/', views.deny_item, name='deny_item'),
    
    # API routes
    path('api/', include(router.urls)),
]