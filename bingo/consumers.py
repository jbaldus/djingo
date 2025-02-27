# bingo/consumers.py
import json
import logging
from asgiref.sync import async_to_sync
from django.template.loader import render_to_string
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Player, BingoGame, GameEvent
import traceback

logger = logging.getLogger(__name__)

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
                
            self.game_group_name = f'game_{self.player.game.id}'
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
            data = json.loads(text_data)
            message_type = data.get('type')
            print(f"Player {self.player} sends {message_type}")
            if message_type == 'mark_position':
                position = data.get('position')
                if position is not None:
                    rendered_html = await self.mark_position(position)
                    await self.send(rendered_html)
                    winner = self.check_win_condition(self.player.covered_positions)
                    print(f"IS WINNER?: {winner}")
                    if winner:
                        # Notify all players about the winner
                        await self.channel_layer.group_send(
                            self.game_group_name,
                            {
                                'type': 'winner_announcement',
                                'winner': self.player.name
                            }
                        )
        
            elif message_type == 'request_state':
                await self.send_game_state()
                
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
        print(f"WINNER: {event['winner']}")
        await self.send(text_data=json.dumps({
            'type': 'winner',
            'winner': event['winner']
        }))

    async def player_event(self, event):
        rendered_html = f'<div hx-swap-oob="afterbegin:#eventsList"><div class="event-item"><span class="event-message">{event['message']}</span></div></div>'
        if event.get("sender") != self.channel_layer:
            await self.send(rendered_html)

    @database_sync_to_async
    def create_event(self, player, message):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                'type': 'player_event',
                'message': message,
                'sender': self.channel_name,
            }
        )

    @database_sync_to_async
    def get_player(self):
        try:
            player = Player.objects.select_related('game').get(id=self.player_id)
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
    def get_recent_events(self, game, limit=10):
        return list(game.events.select_related('player')
                   .values('player__name', 'message', 'created_at')
                   [:limit])

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

    def check_win_condition(self, covered_positions):
        game = self.player.game
        return game.check_win_condition(covered_positions)
