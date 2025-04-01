from django.utils import timezone
from .models import BingoGame, BingoBoard, Player, BingoBoardItem, GameEvent

def get_latest_events(game:BingoGame) -> list:
    lifetime = 60
    now = timezone.now()
    max_age = now - timezone.timedelta(seconds=lifetime)

    recent_events = GameEvent.objects.filter(game=game, created_at__gt=max_age)

    result = [  {
                    'player': event.player,
                    'message': event.message,
                    'remove_in': max(0, (event.created_at - max_age).total_seconds()),
                    'created_at': event.created_at.timestamp() * 1000,
                }
                for event in recent_events
            ]
    return result


def get_all_events(game:BingoGame) -> list:
    recent_events = GameEvent.objects.filter(game=game)

    result = [  {
                    'player': event.player,
                    'message': event.message,
                    'remove_in': 0,
                    'created_at': event.created_at.timestamp() * 1000,
                }
                for event in recent_events
            ]
    return result
