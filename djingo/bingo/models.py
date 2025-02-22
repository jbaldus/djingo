# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
import random

class User(AbstractUser):
    is_administrator = models.BooleanField(default=False)

    # Add related_name attributes to resolve the conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='bingo_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='bingo_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class BingoBoard(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class BingoBoardItem(models.Model):
    board = models.ForeignKey(BingoBoard, related_name='items', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    position = models.IntegerField(null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['board', 'position'],
                name='unique_position_per_board'
            )
        ]

class BingoGame(models.Model):
    board = models.ForeignKey(BingoBoard, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)
    has_free_square = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey('Player', null=True, blank=True, on_delete=models.SET_NULL, related_name='games_won')

    def generate_code(self):
        # Generate a random 6-character code
        chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
        while True:
            code = ''.join(random.choice(chars) for _ in range(6))
            if not BingoGame.objects.filter(code=code).exists():
                return code
            
    def generate_board_layout(self):
        items = list(self.board.items.all().values_list('text', flat=True))
        random.shuffle(items)
        board_layout = items[:25] # Just the first 25
        if self.has_free_square:
            board_layout[12] = "FREE"
        return board_layout

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

class Player(models.Model):
    game = models.ForeignKey(BingoGame, related_name='players', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    board_layout = models.JSONField()  # Stores the randomized board positions
    covered_positions = models.JSONField(default=list)
    has_won = models.BooleanField(default=False)
    is_connected = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'name'],
                name='unique_player_name_per_game'
            )
        ]
