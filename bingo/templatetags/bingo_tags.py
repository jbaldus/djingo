from django import template

register = template.Library()

@register.filter(name='zip')
def zip_lists(a, b):
    return zip(a, b)

@register.inclusion_tag('bingo/partials/bingo_board.html')
def bingo_board(player, game):
    context = {
        'player': player,
        'game': game,
        'board_items': player.board_layout,
        'board_positions': range(player.game.board_size * player.game.board_size)
    }
    print("Bingo Board Tag Included")
    return context

@register.inclusion_tag('bingo/partials/bingo_cell.html')
def bingo_cell(item, position, player, game):
    """Renders a bingo cell with appropriate attributes."""

    covered = position in player.covered_positions
    free = (
        game.has_free_square
        and game.board_size == 5
        and position == 12
    )

    # Create the context for the bingo_cell.html template
    context = {
        'text': item,
        'position': position,
        'covered': covered,
        'free': free,
        'player_id': player.id  # Add player ID to the context
    }
    return context

@register.inclusion_tag('bingo/partials/event_item.html')
def event_item(event):
    context = { 
        'player': event['player'],
        'message': event['message'],
        'remove_in': event['remove_in'],
    }
    return context