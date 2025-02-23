# bingo/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import BingoGame, BingoBoard, Player
from .forms import LoginForm, PlayerNameForm
import json
import logging

logger = logging.getLogger(__name__)


def home(request):
    context = {
        'recent_name': request.COOKIES.get('player_name', '')
    }
    
    if request.user.is_authenticated:
        context.update({
            'boards': BingoBoard.objects.filter(creator=request.user).order_by('-created_at'),
            'games': BingoGame.objects.filter(creator=request.user).order_by('-created_at')
        })
    
    return render(request, 'bingo/home.html', context)

def join_game(request, code):
    game = get_object_or_404(BingoGame, code=code, is_active=True)
    
    if request.method == 'POST':
        form = PlayerNameForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']

            # Check for existing player
            existing_player = Player.objects.filter(name=name, game=game).first()
            if existing_player:
                # Redirect to existing player's game
                return redirect('play_game', player_id=existing_player.id)

            player = Player.objects.create(
                game=game,
                name=form.cleaned_data['name'],
                board_layout=game.generate_board_layout(),
                covered_positions=[12] if game.has_free_square else []
            )
            
            response = redirect('play_game', player_id=player.id)
            response.set_cookie('player_name', form.cleaned_data['name'], max_age=30*24*60*60)  # 30 days
            return response
    else:
        form = PlayerNameForm(initial={'name': request.COOKIES.get('player_name', '')})
    
    return render(request, 'bingo/join_game.html', {
        'game': game,
        'form': form
    })

def play_game(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    if not player.game.is_active and not player.has_won:
        return redirect('home')
    
    return render(request, 'bingo/play_game.html', {
        'player': player,
        'game': player.game,
        'board_items': list(player.board_layout),
        'events': player.game.events.select_related('player')[:10]
    })

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
    
    return render(request, 'bingo/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@require_http_methods(["POST"])
def mark_position(request, player_id):
    logger.info(f"Marking position for player {player_id}")
    try:
        # Log request body
        logger.debug(f"Request body: {request.body}")
        
        # Get player
        player = get_object_or_404(Player, id=player_id)
        logger.debug(f"Found player: {player.name}")
        
        # Parse JSON
        try:
            data = json.loads(request.body)
            position = data.get('position')
            logger.debug(f"Position to mark: {position}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        
        if position is None:
            logger.error("No position provided in request")
            return JsonResponse({'error': 'Position is required'}, status=400)
        
        # Log current covered positions
        logger.debug(f"Current covered positions: {player.covered_positions}")
        
        # Check if position is already covered
        if position in player.covered_positions:
            logger.debug(f"Position {position} already covered")
            try:
                player.covered_positions.remove(position)
                player.save()
            except ValueError:
                pass
            return JsonResponse({
                'status': 'already_marked',
                'positions': player.covered_positions
            })
            
        # Add new position
        try:
            if not isinstance(player.covered_positions, list):
                logger.warning(f"covered_positions is not a list: {type(player.covered_positions)}")
                player.covered_positions = []
            
            player.covered_positions.append(position)
            player.save()
            logger.debug(f"Added position {position}. New covered positions: {player.covered_positions}")
            
        except Exception as e:
            logger.exception("Error updating covered positions")
            return JsonResponse({'error': 'Error updating game state'}, status=500)
            
        # Check win condition
        try:
            if check_win_condition(player.covered_positions):
                logger.info(f"Player {player.name} has won!")
                player.has_won = True
                player.game.winner = player
                #player.game.is_active = False
                player.game.save()
                player.save()
                
                return JsonResponse({
                    'status': 'win',
                    'winner': player.name
                })
        except Exception as e:
            logger.exception("Error checking win condition")
            return JsonResponse({'error': 'Error checking win condition'}, status=500)
        
        return JsonResponse({
            'status': 'marked',
            'positions': player.covered_positions
        })
        
    except Player.DoesNotExist:
        logger.error(f"Player {player_id} not found")
        return JsonResponse({'error': 'Player not found'}, status=404)
    except Exception as e:
        logger.exception("Unexpected error in mark_position")
        return JsonResponse({'error': str(e)}, status=500)
    
def check_win_condition(covered_positions):
    winning_patterns = [
        # Rows
        [0,1,2,3,4], [5,6,7,8,9], [10,11,12,13,14], [15,16,17,18,19], [20,21,22,23,24],
        # Columns
        [0,5,10,15,20], [1,6,11,16,21], [2,7,12,17,22], [3,8,13,18,23], [4,9,14,19,24],
        # Diagonals
        [0,6,12,18,24], [4,8,12,16,20]
    ]
    #winning_patterns = [ list(range(25)) ]
    covered_set = set(covered_positions)
    return any(all(pos in covered_set for pos in pattern) for pattern in winning_patterns)

@require_http_methods(["POST"])
def clear_board(request, player_id):
    try:
        logger.info("Trying to clear board for player {player_id}")
        player = get_object_or_404(Player, id=player_id)
        
        # Reset player's board
        if player.game.has_free_square:
            player.covered_positions = [12]  # Keep only center square if it's a free square game
        else:
            player.covered_positions = []
            
        player.has_won = False
        player.board_layout = player.game.generate_board_layout()
        player.save()
        
        return JsonResponse({
            'status': 'cleared',
            'covered_positions': player.covered_positions,
            'board_items': list(player.board_layout)
        })
        
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)
    except Exception as e:
        logger.exception("Error clearing board")
        return JsonResponse({'error': str(e)}, status=500)


def create_game(request):
    if request.method == 'POST':
        form = CreateGameForm(request.POST)
        if form.is_valid():
            game = form.save(commit=False)
            game.creator = request.user
            game.save()
            return redirect('game_details', code=game.code)
    else:
        form = CreateGameForm()
    
    return render(request, 'bingo/create_game.html', {'form': form})