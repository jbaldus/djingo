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
    game = player.game
    if not game.is_active and not player.has_won:
        return redirect('home')
    
    return render(request, 'bingo/play_game.html', {
        'player': player,
        'game': game,
        'board_items': list(player.board_layout),
        'board_positions': range(game.board_size*game.board_size)
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