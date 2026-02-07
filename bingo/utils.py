import random

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


def generate_silly_nickname(game:BingoGame, unique:bool = True) -> str:
    CUTE_ADJECTIVES = [
        'Bouncy', 'Bubblegum', 'Bubbly', 'Cherry', 'Chirpy', 
        'Cloudy', 'Cosmic', 'CottonCandy', 'Cozy', 'Cuddly', 
        'Cupcake', 'Dreamy', 'Fluffy', 'Fuzzy', 'Gentle', 
        'Giggly', 'Glittery', 'Honey', 'Jellybean', 
        'Jolly', 'Lucky', 'Marshmallow', 'Misty', 'Peachy', 
        'Peppermint', 'Poppy', 'Pudding', 'Puffy', 'Rainbow', 
        'Sleepy', 'Snowy', 'Snuggly', 'Soft', 'Sparkly', 
        'Spirited', 'Sprinkled', 'Starry', 'Sugar', 'Sunny', 
        'SunnySide', 'Tiny', 'Toasty', 'Twinkly', 'Whimsical', 
        'Wiggly',
    ]

    CUTE_ANIMALS = [
        'Badger', 'Bluebird', 'Bunny', 'Chinchilla', 'Corgi', 
        'Dolphin', 'Duckling', 'Fawn', 'Fennec', 'Firefly', 
        'Fox', 'Giraffe', 'Goldfish', 'Goose', 'Hamster', 
        'Hedgehog', 'Hummingbird', 'Kitten', 'Koala', 
        'Ladybug', 'Llama', 'Meerkat', 'Mole', 'Mouse', 
        'Narwhal', 'Otter', 'Owlet', 'Panda', 'Panda', 
        'Penguin', 'Piglet', 'Platypus', 'PolarBear', 'Puffin', 
        'Puppy', 'Raccoon', 'Ravioli', 'RedPanda', 'Robin', 
        'Seal', 'SnowLeopard', 'Songbird', 'Squirrel', 
        'Turtle', 'Unicorn',
    ]

    CUTE_EMOJIS = [
        "✨", "🌟", "💫", "🎉", "🍰", "🍪", "🍩",
        "🎊", "🌈", "🌻", "🌸", "🌠", "🪄", "🏳️", 
        "🏴", "🎌", "🍬", "🍭", "🍫", "🪅", "🍨",
        "🍦", "🧁", "☄️", "🥞", "🍕", "🍟", "🧇", 
        "✴️", "☀️", "🪐", "🌙", "💖", "💗", "🏵️",
        "🌼","🪷",
    ]

    adj = random.choice(CUTE_ADJECTIVES)
    animal = random.choice(CUTE_ANIMALS)
    emoji = random.choice(CUTE_EMOJIS)
    cute_name = f"{adj} {animal} {emoji}"
    if not unique or game is None:
        return cute_name
    players = game.players.all()
    player_names = [player.name for player in players]
    while cute_name in player_names:
        adj = random.choice(CUTE_ADJECTIVES)
        animal = random.choice(CUTE_ANIMALS)
        emoji = random.choice(CUTE_EMOJIS)
        cute_name = f"{adj} {animal} {emoji}"
    return cute_name
