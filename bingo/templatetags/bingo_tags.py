from django import template

register = template.Library()

@register.filter(name='zip')
def zip_lists(a, b):
    return zip(a, b)

@register.inclusion_tag('bingo/partials/bingo_board.html')
def bingo_board(player):
    context = {
        'player': player,
        'game': player.game,
        'board_items': player.board_layout,
        'board_positions': range(player.game.board_size * player.game.board_size)
    }
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

