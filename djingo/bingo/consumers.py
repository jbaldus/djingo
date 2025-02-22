# bingo/consumers.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from .models import Player, BingoGame

logger = logging.getLogger(__name__)

class BingoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.player_id = self.scope['url_route']['kwargs']['player_id']
            self.player = await self.get_player()
            
            if not self.player:
                logger.error(f"Player {self.player_id} not found")
                await self.close(code=4004)  # Custom close code for invalid player
                return
            
            if not self.player.game.is_active:
                logger.info(f"Attempted to connect to inactive game: {self.player.game.id}")
                await self.close(code=4005)  # Custom close code for inactive game
                return
            
            self.game_group_name = f'game_{self.player.game.id}'

            # Join game group
            await self.channel_layer.group_add(
                self.game_group_name,
                self.channel_name
            )

            # Mark player as connected in database
            await self.set_player_connection_status(True)
            
            await self.accept()
            
            # Send initial game state
            await self.send_game_state()
            
        except Exception as e:
            logger.exception("Error in WebSocket connect")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'game_group_name'):
                await self.channel_layer.group_discard(
                    self.game_group_name,
                    self.channel_name
                )
            
            if hasattr(self, 'player'):
                await self.set_player_connection_status(False)
                
        except Exception as e:
            logger.exception("Error in WebSocket disconnect")
        finally:
            raise StopConsumer()

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
            elif message_type == 'request_game_state':
                await self.send_game_state()
            
        except json.JSONDecodeError:
            logger.error("Received invalid JSON")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))
        except Exception as e:
            logger.exception("Error in WebSocket receive")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))

    async def game_update(self, event):
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            logger.exception("Error sending game update")

    async def winner_announcement(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type': 'winner',
                'winner': event['winner']
            }))
        except Exception as e:
            logger.exception("Error sending winner announcement")

    @database_sync_to_async
    def get_player(self):
        try:
            return Player.objects.select_related('game').get(id=self.player_id)
        except Player.DoesNotExist:
            return None

    @database_sync_to_async
    def set_player_connection_status(self, is_connected):
        try:
            Player.objects.filter(id=self.player_id).update(is_connected=is_connected)
        except Exception as e:
            logger.exception("Error updating player connection status")

    async def send_game_state(self):
        try:
            game_state = await self.get_game_state()
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'data': game_state
            }))
        except Exception as e:
            logger.exception("Error sending game state")

    @database_sync_to_async
    def get_game_state(self):
        game = self.player.game
        return {
            'game_id': game.id,
            'is_active': game.is_active,
            'winner': game.winner.name if game.winner else None,
            'connected_players': list(game.players.filter(is_connected=True).values_list('name', flat=True))
        }