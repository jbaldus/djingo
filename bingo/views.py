# bingo/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import BingoGame, BingoBoard, Player, BingoBoardItem, GameEvent
from .forms import LoginForm, PlayerNameForm, FeedbackForm
from .utils import get_latest_events, get_all_events
import logging

logger = logging.getLogger(__name__)


def home(request):
    context = {
        'games': BingoGame.objects.filter(is_active=True).exclude(is_private=True).order_by('-created_at'),
    }
    
    if request.user.is_authenticated:
        context.update({
            'boards': BingoBoard.objects.filter(creator=request.user).order_by('-created_at'),
            # 'games': BingoGame.objects.filter(creator=request.user).order_by('-created_at')
        })
    
    return render(request, 'bingo/home.html', context)

def view_404(request, exception=None):
    return redirect('/')

def join_game(request, code):
    code = code.upper()
    game = get_object_or_404(BingoGame, code=code, is_active=True)
    
    if request.method == 'POST':
        form = PlayerNameForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            use_suggested_items = form.cleaned_data['use_suggested_items']
            player_id = request.COOKIES.get('player_id')
            player = None
            try:
                player = Player.objects.get(id=player_id)
                if player.name != name:
                    player.name = name
                    player.use_suggested_items = use_suggested_items
                    player.save()
                if not player.game.is_active or game != player.game:
                    player = None
                elif player.game == game:
                    return redirect('play_game', player_id=player.id)

            except Player.DoesNotExist:
                pass

            if player is None:
                player = Player.objects.create(
                    game=game,
                    name=form.cleaned_data['name'],
                    board_layout=game.generate_board_layout(use_suggested_items),
                    covered_positions=[12] if game.has_free_square else [],
                    use_suggested_items=use_suggested_items,
                )
            
            response = redirect('play_game', player_id=player.id)
            response.set_cookie('player_id', player.id, max_age=30*24*60*60)  # 30 days
            return response
    else:
        player_id = request.COOKIES.get('player_id')
        player = Player.objects.filter(id=player_id)
        try:
            player = Player.objects.get(id=player_id)
            if player.game == game:
                    return redirect('play_game', player_id=player.id)
            form = PlayerNameForm(initial={'name': player.name})
        except Player.DoesNotExist:
            form = PlayerNameForm()

        return render(request, 'bingo/join_game.html', {
            'game': game,
            'form': form
        })


def play_game(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    game = player.game
    if not game.is_active and not player.has_won:
        return redirect('home')
    join_path = reverse('join_game', kwargs={'code': game.code})
    share_url = request.build_absolute_uri(join_path)
    events = get_latest_events(game)
    
    return render(request, 'bingo/play_game.html', {
        'player': player,
        'game': game,
        'board_items': list(player.board_layout),
        'board_positions': range(game.board_size*game.board_size),
        'url': share_url,
        'events': events,
    })

def spectate(request, code):
    game = get_object_or_404(BingoGame, code=code)
    events = get_all_events(game=game)
    context = {
        'game': game,
        'events': events,
    }
    return render(request, 'bingo/spectate.html', context=context)

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

@staff_member_required
def review_suggestions(request):
    items = BingoBoardItem.objects.exclude(suggested_by='').filter(approved__isnull=True)
    return render(request, 'admin/bingo/review_suggestions.html', {'items': items})

@staff_member_required
def approve_item(request, item_id):
    item = BingoBoardItem.objects.get(id=item_id)
    item.approved = True
    item.save()
    return HttpResponse('')

@staff_member_required
def deny_item(request, item_id):
    item = BingoBoardItem.objects.get(id=item_id)
    item.approved = False
    item.save()
    return HttpResponse('')

def share_game(request: HttpRequest, player_id: int):
    try:
        player: Player = get_object_or_404(Player, id=player_id)
        game: BingoGame = player.game
        join_path = reverse('join_game', kwargs={'code': game.code})
        full_url = request.build_absolute_uri(join_path)

        context = { 'url': full_url }
        return render(request, 'bingo/partials/share_game.html', context)
                
    except Player.DoesNotExist:
        return JsonResponse({'error': 'Player not found'}, status=404)
    
def submit_feedback(request: HttpRequest, player_id: int):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=True)
            return render(request, "bingo/partials/feedback_accepted.html", context={'feedback': feedback})
    else:
        try:
            player = Player.objects.get(id=player_id)
            game = player.game
            initial = {
                'name': player.name,
                'game_code': game.code,
                'game_name': game.name,
            }
            form = FeedbackForm(initial=initial)
        except Player.DoesNotExist:
            form = FeedbackForm()
        val = render(request, "bingo/partials/feedback_form.html", context={"form": form})
        print(val)
        return val

