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
    BOARD_SIZE_CHOICES = [
        (4, '4x4'),
        (5, '5x5'),
    ]
    
    WIN_CONDITION_CHOICES = [
        ('traditional', 'Traditional (line)'),
        ('all', 'All Squares'),
    ]
    
    board = models.ForeignKey(BingoBoard, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)
    has_free_square = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    winner = models.ForeignKey('Player', null=True, blank=True, on_delete=models.SET_NULL, related_name='games_won')
    board_size = models.IntegerField(choices=BOARD_SIZE_CHOICES, default=5)
    win_condition = models.CharField(
        max_length=20, 
        choices=WIN_CONDITION_CHOICES,
        default='traditional'
    )

    def generate_code(self):
        # Generate a random 6-character code
        chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
        while True:
            code = ''.join(random.choice(chars) for _ in range(6))
            if not BingoGame.objects.filter(code=code).exists():
                return code

    def generate_board_layout(self):
        """Generate a randomized board layout based on board size"""
        items = list(self.board.items.all().values_list('id', flat=True))
        random.shuffle(items)
        return items[:(self.board_size * self.board_size)]

    def get_center_position(self):
        """Get the center position based on board size"""
        if self.board_size == 4:
            return None  # 4x4 boards don't have a true center
        return 12  # Center of 5x5 board

    def check_win_condition(self, covered_positions):
        """Check if the covered positions constitute a win"""
        if self.win_condition == 'all':
            # All squares must be covered
            return len(covered_positions) == (self.board_size * self.board_size)
        
        # Traditional win conditions (lines)
        size = self.board_size
        
        # Generate winning patterns based on board size
        winning_patterns = []
        
        # Rows
        for i in range(size):
            winning_patterns.append(list(range(i * size, (i + 1) * size)))
        
        # Columns
        for i in range(size):
            winning_patterns.append(list(range(i, size * size, size)))
        
        # Diagonals
        winning_patterns.append(list(range(0, size * size, size + 1)))  # Top-left to bottom-right
        winning_patterns.append(list(range(size - 1, size * (size - 1) + 1, size - 1)))  # Top-right to bottom-left
        
        covered_set = set(covered_positions)
        return any(all(pos in covered_set for pos in pattern) for pattern in winning_patterns)

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
        
class GameEvent(models.Model):
    game = models.ForeignKey(BingoGame, related_name='events', on_delete=models.CASCADE)
    player = models.ForeignKey(Player, related_name='events', on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']