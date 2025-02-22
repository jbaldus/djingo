# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import BingoGame, Player
import json
import random

def join_game(request, code):
    game = get_object_or_404(BingoGame, code=code, is_active=True)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            # Create randomized board layout
            items = list(game.board.items.all().values_list('id', flat=True))
            random.shuffle(items)
            board_layout = items[:25] # Just the first 25 items
            
            # If there's a free square, ensure the center position is marked
            initial_covered = []
            if game.has_free_square:
                initial_covered = [12]  # Center position (0-based)
                board_layout[12] = "FREE"
            
            player = Player.objects.create(
                game=game,
                name=name,
                board_layout=board_layout,
                covered_positions=initial_covered
            )
            return redirect('play_game', player_id=player.id)
    return render(request, 'bingo/join_game.html', {'game': game})

def play_game(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    game = player.game

    # Add game logic here
    # For example, you might want to check if the game has started,
    # retrieve the player's board, check for wins, etc.

    context = {
        'player': player,
        'game': game,
        'board_items': player.board_layout,
        'covered_positions': player.covered_positions,
        # Add other necessary context data
    }

    return render(request, 'bingo/play_game.html', context)

@require_http_methods(['POST'])
def mark_position(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    data = json.loads(request.body)
    position = data.get('position')
    
    if position not in player.covered_positions:
        player.covered_positions.append(position)
        player.save()
        
        # Check for win condition
        if check_win_condition(player.covered_positions):
            player.has_won = True
            player.game.winner = player
            player.game.is_active = False
            player.game.save()
            player.save()
            
            # Notify all players about the winner
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'game_{player.game.id}',
                {
                    'type': 'winner_announcement',
                    'winner': player.name
                }
            )
            
            return JsonResponse({'status': 'win', 'winner': player.name})
    
    return JsonResponse({'status': 'marked'})


def check_win_condition(covered_positions):
    # Define winning patterns (rows, columns, diagonals)
    winning_patterns = [
        # Rows
        [0,1,2,3,4], [5,6,7,8,9], [10,11,12,13,14], [15,16,17,18,19], [20,21,22,23,24],
        # Columns
        [0,5,10,15,20], [1,6,11,16,21], [2,7,12,17,22], [3,8,13,18,23], [4,9,14,19,24],
        # Diagonals
        [0,6,12,18,24], [4,8,12,16,20]
    ]
    
    covered_set = set(covered_positions)
    return any(all(pos in covered_set for pos in pattern) for pattern in winning_patterns)
