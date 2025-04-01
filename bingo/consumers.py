# bingo/consumers.py
import json
import logging
from asgiref.sync import async_to_sync
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Player, BingoGame, BingoBoardItem, GameEvent
from .forms import SuggestionForm, PlayerNameChangeForm

logger = logging.getLogger(__name__)

class SpectatorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f"Attempting to connect spectator to game...")
        try:
            self.code = self.scope['url_route']['kwargs']['game_code']
            self.game = await self.get_game()
            self.game_group_name = f'game_{self.game.code}'
            await self.channel_layer.group_add(
                self.game_group_name,
                self.channel_name
            )
            await self.accept()
            self.send(text_data="Welcome")
        except BingoGame.DoesNotExist:
            logger.error(f"Game not found for spectator with code {self.code}")
            return
            
        except Exception as e:
            logger.exception(f"Error in connect for game {self.code}: {e}")
            await self.close(code=4000)
        
    async def disconnect(self, close_code):
        logger.info(f"Disconnecting spectator, code: {close_code}")
        try:
            if hasattr(self, 'game_group_name'):
                await self.channel_layer.group_discard(
                    self.game_group_name,
                    self.channel_name
                )
                            
        except Exception as e:
            logger.exception("Error in disconnect")

    @database_sync_to_async
    def get_game(self):
        try:
            game: BingoGame = BingoGame.objects.get(code=self.code)
            logger.info(f"Found game: {game.name} for game: {game.code}")
            return game
        except BingoGame.DoesNotExist:
            logger.error(f"Game {self.code} not found")
            return None
        except Exception as e:
            logger.exception(f"Error getting game {self.code}")
            return None


    async def player_event(self, event):
        game_event = event['game_event']
        game_event['remove_in'] = 0
        event_html : str = render_to_string("bingo/partials/event_item.html", context={'event': game_event})
        print(event_html)
        
        rendered_html = f'<div hx-swap-oob="afterbegin:#events-list">{event_html}</div>'
        print(rendered_html)
        # rendered_html : str= f'<div hx-swap-oob="afterbegin:#events-list"><div class="event-item" remove-me="90s"><span class="event-message {event.get('class', '')}">{event['message']}</span></div></div>'
        await self.send(rendered_html)

            

class BingoGameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(f"Attempting connection for player_id: {self.scope['url_route']['kwargs'].get('player_id')}")
        
        try:
            self.player_id = self.scope['url_route']['kwargs']['player_id']
            self.player = await self.get_player()
            
            if not self.player:
                logger.error(f"No player found with ID: {self.player_id}")
                await self.close(code=4004)
                return
            
            if not self.player.game.is_active:
                rendered_html = render_to_string("bingo/partials/inactive_game_modal.html")
                await self.send(rendered_html)
                return
                
            self.game_group_name = f'game_{self.player.game.code}'
            logger.info(f"Player {self.player_id} joining game group: {self.game_group_name}")

            # Join game group
            await self.channel_layer.group_add(
                self.game_group_name,
                self.channel_name
            )

            await self.accept()
            logger.info(f"Connection accepted for player {self.player_id}")
            
            # Send initial game state
            await self.send_game_state()
            
        except Exception as e:
            logger.exception(f"Error in connect for player_id {self.player_id}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        logger.info(f"Disconnecting player {getattr(self, 'player_id', 'unknown')}, code: {close_code}")
        try:
            if hasattr(self, 'game_group_name'):
                await self.channel_layer.group_discard(
                    self.game_group_name,
                    self.channel_name
                )
            
            if hasattr(self, 'player'):
                await self.update_player_connection_status(False)
                
        except Exception as e:
            logger.exception("Error in disconnect")

    async def receive(self, text_data):
        try:
            player = await self.get_player()
            if not player.game.is_active:
                rendered_html = render_to_string("bingo/partials/inactive_game_modal.html")
                await self.send(rendered_html)
                return
            data = json.loads(text_data)
            message_type = data.get('type')
            if message_type == 'mark_position':
                player = await self.get_player()
                position = data.get('position')
                if position is not None:
                    rendered_html = await self.mark_position(position)
                    await self.send(rendered_html)
                    winner = await self.check_win_condition()
                    if winner:
                        await self.create_event(
                            player=player,
                            message=f"{player.name} has won the game!! 🎉<br/>You can keep playing, though."
                        )
                        context : dict = { 'player': player}
                        rendered_html : str = render_to_string("bingo/partials/winner_modal.html", context)
                        await self.send(rendered_html)
        
            elif message_type == 'request_state':
                await self.send_game_state()
            elif message_type == 'clear_board':
                await self.start_new_game()
            elif message_type == 'make_suggestions':
                context : dict = { 'form': SuggestionForm(), }
                rendered_html : str = render_to_string("bingo/partials/suggestions_modal.html", context)
                await self.send(rendered_html)
            elif message_type == 'submit_suggestions':
                await self.process_suggestions(data)
                await self.start_new_game()
            elif message_type == 'confirm_abandon_board':
                rendered_html : str = render_to_string("bingo/partials/confirm_abandon_board_modal.html")
                await self.send(rendered_html)
            elif message_type == 'abandon_board':
                message = f"{player.name} is giving up on their board and starting over"
                await self.create_event(player=player, message=message)
                await self.start_new_game()
            elif message_type == 'change_name_form':
                context : dict = {
                   'form': PlayerNameChangeForm(),
                   'consumer_message': 'change_name',
                   'message': '',
                   'title': 'Change Name',
                   'submit_text': 'Change Name', 
                }
                rendered_html : str = render_to_string("bingo/partials/modal.html", context)
                await self.send(rendered_html)
            elif message_type == 'change_name':
                player_name = await self.process_name_change(data)
                rendered_html : str = f'<div hx-target="#player-info" hx-swap="outerHTML" id="player-info" class="player-info">Playing as: <strong>{player_name}</strong></div>'
                await self.close_sidebar()
                await self.send(rendered_html)

                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))

    async def game_update(self, event):
        # Send game update to WebSocket
        await self.send(text_data=json.dumps(event))

    async def winner_announcement(self, event):
        # Send winner announcement to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'winner',
            'winner': event['winner']
        }))

    async def player_event(self, event):
        player : Player = await self.get_player()
        game_event = event['game_event']
        game_event['remove_in'] = 90
        event_html : str = render_to_string("bingo/partials/event_item.html", context={'event': game_event})
        rendered_html = f'<div hx-swap-oob="afterbegin:#events-list">{event_html}</div>'
        if event.get("sender") != self.channel_name or player.show_own_events: 
            await self.send(rendered_html)

    async def clear_modal(self):
        empty_modal = '<div id="theModal" hx-target="#theModal" hx-swap="outerHTML"></div>'
        await self.send(empty_modal)
    
    async def do_javascript(self, javascript:str):
        close_script = f'<div id="immediateScript" hx-target="#immediateScript" hx-swap="outerHTML"><script>{javascript}</script></div>'
        await self.send(close_script)

    async def close_sidebar(self):
        await self.do_javascript('document.getElementById("sidebar").classList.remove("show");')

    async def start_new_game(self) -> Player:
        player : Player = await self.clear_board()
        context = { 
            'player': player,
            'game': player.game,
            'board_items': player.board_layout,
            'board_positions': range(player.game.board_size * player.game.board_size),
        }
        rendered_html = render_to_string("bingo/partials/bingo_board.html", context=context)
        await self.send(rendered_html)
        await self.clear_modal()
        await self.close_sidebar()
        return player
    
    @database_sync_to_async
    def create_event(self, player, message):
        game_event = {
            'player': player.name,
            'message': message,
            'created_at': timezone.now().timestamp()*1000,
        }
        if not getattr(settings, 'FORGET_GAME_EVENTS', False):
            game_event_object = GameEvent.objects.create(
                game=player.game,
                player=player,
                message=message
            )

        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                'type': 'player_event',
                'game_event': game_event,
                'sender': self.channel_name,
            }
        )

    @database_sync_to_async
    def get_player(self):
        try:
            player: Player = Player.objects.select_related('game').get(id=self.player_id)
            logger.info(f"Found player: {player.name} for game: {player.game.code}")
            return player
        except Player.DoesNotExist:
            logger.error(f"Player {self.player_id} not found")
            return None
        except Exception as e:
            logger.exception(f"Error getting player {self.player_id}")
            return None

    @database_sync_to_async
    def update_player_connection_status(self, is_connected):
        Player.objects.filter(id=self.player_id).update(is_connected=is_connected)
    
    @database_sync_to_async
    def clear_board(self) -> Player:
        player : Player = Player.objects.select_related('game').get(id=self.player_id)
        game : BingoGame = player.game
        player.board_layout = game.generate_board_layout()
        player.covered_positions = []
        if game.has_free_square and game.get_center_position():
            player.covered_positions = [ game.get_center_position() ]
            player.board_layout[game.get_center_position()] = "FREE"
        player.has_won = False
        player.save()
        return player

    @database_sync_to_async
    def mark_position(self, position):
        player = Player.objects.get(id=self.player_id)
        game = player.game
        position = int(position)
        
        if not game.is_active or player.has_won:
            return False
            
        if position not in player.covered_positions:
            action = "marked"
            player.covered_positions.append(position)
            player.save()
        else:
            action = "unmarked"
            player.covered_positions.remove(position)
            player.save()
        
        cell = {
            'position': position,
            'covered': position in player.covered_positions,
            'text': player.board_layout[position],
            'free': (position == 12 and game.has_free_square and game.size == 5),
        }

        # Create event
        async_to_sync(self.create_event)(
            player=player,
            message=f"{player.name} {action} '{player.board_layout[position]}'"
        )

        rendered_html = render_to_string('bingo/partials/bingo_cell.html', cell) 
        return rendered_html  

    @database_sync_to_async
    def get_game_state(self):
        player = Player.objects.get(id=self.player_id)
        game = player.game
        
        return {
            'type': 'game_state',
            'is_active': game.is_active,
            'has_won': player.has_won,
            'winner': game.winner.name if game.winner else None,
            'covered_positions': player.covered_positions,
            'connected_players': list(game.players.filter(
                is_connected=True).values_list('name', flat=True))
        }

    async def send_game_state(self):
        state = await self.get_game_state()
        await self.send(text_data=json.dumps(state))

    async def check_win_condition(self):
        player = await self.get_player()
        game = player.game
        return game.check_win_condition(player.covered_positions)
    
    @database_sync_to_async
    def process_suggestions(self, data):
        form = SuggestionForm(data)
        if form.is_valid():
            suggestions = [
                form.cleaned_data['suggestion1'],
                form.cleaned_data['suggestion2'],
                form.cleaned_data['suggestion3'],
            ]
            suggestions = [s.lower() for s in suggestions if s.strip() != '']
            if not suggestions:
                return
            player = Player.objects.get(id=self.player_id)
            game = player.game
            board = game.board
            # Implement some check for duplication here
            for suggestion in suggestions:
                if board.items.filter(text=suggestion):
                    continue
                BingoBoardItem.objects.create(
                    board=board,
                    text=suggestion,
                    suggested_by=player.name,
                )


    @database_sync_to_async
    def process_name_change(self, data):
        form = PlayerNameChangeForm(data)
        if form.is_valid():
            new_name = form.cleaned_data['name']
            player = Player.objects.get(id=self.player_id)
            if player.name != new_name:
                player.name = new_name
                player.save()
            return player.name
            

