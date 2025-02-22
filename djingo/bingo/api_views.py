# bingo/api_views.py
from rest_framework import viewsets, permissions
from .models import BingoBoard, BingoGame
from .serializers import BingoBoardSerializer, BingoGameSerializer

class BingoBoardViewSet(viewsets.ModelViewSet):
    serializer_class = BingoBoardSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BingoBoard.objects.filter(creator=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

class BingoGameViewSet(viewsets.ModelViewSet):
    serializer_class = BingoGameSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return BingoGame.objects.filter(creator=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)