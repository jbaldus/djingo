# bingo/serializers.py
from rest_framework import serializers
from .models import BingoBoard, BingoGame, BingoBoardItem

class BingoBoardItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BingoBoardItem
        fields = ['text', 'suggested_by', 'approved']

class BingoBoardSerializer(serializers.ModelSerializer):
    items = BingoBoardItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = BingoBoard
        fields = ['id', 'name', 'created_at', 'items']
        read_only_fields = ['created_at']

class BingoGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = BingoGame
        fields = ['id', 'name', 'code', 'board', 'has_free_square', 'is_active', 'created_at']
        read_only_fields = ['code', 'created_at']
