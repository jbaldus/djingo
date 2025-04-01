# bingo/admin.py
import csv
import json
from datetime import datetime
from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.core.exceptions import ValidationError
from .models import User, BingoBoard, BingoBoardItem, BingoGame, Player, GameEvent
from .forms import BingoBoardForm, BingoBoardItemFormSet

@admin.register(GameEvent)
class GameEventAdmin(admin.ModelAdmin):
    list_display = ('player__name', 'game__code', 'message', 'created_at')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_administrator', 'date_joined', 'last_login')
    list_filter = ('is_administrator', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)

class BingoBoardItemInline(admin.TabularInline):
    model = BingoBoardItem
    extra = 1
    min_num = 25
    validate_min = True

@admin.register(BingoBoard)
class BingoBoardAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'created_at', 'item_count', 'times_used')
    list_filter = ('created_at', 'creator')
    search_fields = ('name', 'creator__username')
    inlines = [BingoBoardItemInline]
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:board_id>/duplicate/',
                self.admin_site.admin_view(self.duplicate_board),
                name='bingo_board_duplicate',
            ),
            path(
                'import/',
                self.admin_site.admin_view(self.import_board),
                name='bingo_board_import',
            ),
            path(
                '<int:board_id>/export/csv/',
                self.admin_site.admin_view(self.export_board_csv),
                name='bingo_board_export_csv',
            ),
            path(
                '<int:board_id>/export/json/',
                self.admin_site.admin_view(self.export_board_json),
                name='bingo_board_export_json',
            ),
        ]
        return custom_urls + urls
        
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Number of Items'
    
    def times_used(self, obj):
        return BingoGame.objects.filter(board=obj).count()
    times_used.short_description = 'Times Used in Games'
    
    def duplicate_board(self, request, board_id):
        board = get_object_or_404(BingoBoard, id=board_id)
        new_board = BingoBoard.objects.create(
            name=f"Copy of {board.name}",
            creator=request.user
        )
        
        for item in board.items.all():
            BingoBoardItem.objects.create(
                board=new_board,
                text=item.text
            )
        
        messages.success(request, f"Successfully duplicated board '{board.name}'")
        return HttpResponseRedirect(
            reverse('admin:bingo_bingoboard_change', args=[new_board.id])
        )
    
    def import_board(self, request):
        if request.method == 'POST':
            try:
                file = request.FILES.get('file')
                if not file:
                    raise ValidationError('No file uploaded')

                file_format = request.POST.get('format')
                board_name = request.POST.get('board_name')

                if not board_name:
                    raise ValidationError('Board name is required')

                items = []
                if file_format == 'csv':
                    decoded_file = file.read().decode('utf-8').splitlines()
                    reader = csv.DictReader(decoded_file)
                    items = [row['text'] for row in reader if row.get('text')]
                elif file_format == 'json':
                    data = json.load(file)
                    items = [item['text'] for item in data.get('items', [])]
                elif file_format == 'txt':
                    decoded_file = file.read().decode('utf-8').splitlines()
                    items = [line for line in decoded_file if line.strip() != ""]
                else:
                    raise ValidationError('Invalid file format')

                if len(items) < 25:
                    raise ValidationError('Board must have at least 25 items')

                # Create new board
                board = BingoBoard.objects.create(
                    name=board_name,
                    creator=request.user
                )

                # Create board items
                for text in items:
                    print(text)
                    BingoBoardItem.objects.create(
                        board=board,
                        text=text,
                    )

                messages.success(request, f'Successfully imported board "{board_name}" with {len(items)} items')
                return HttpResponseRedirect(
                    reverse('admin:bingo_bingoboard_change', args=[board.id])
                )

            except (ValidationError, json.JSONDecodeError, csv.Error) as e:
                messages.error(request, f'Error importing board: {str(e)}')
            except Exception as e:
                messages.error(request, 'An unexpected error occurred during import')

        return TemplateResponse(
            request,
            'admin/bingo/bingoboard/import.html',
            context=self.admin_site.each_context(request)
        )

    def export_board_csv(self, request, board_id):
        board = self.get_object(request, board_id)
        if not board:
            return JsonResponse({'error': 'Board not found'}, status=404)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="bingo_board_{board.name}_{datetime.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(['text', 'suggested_by'])
        
        for item in board.items.all():
            writer.writerow([item.text, item.suggested_by])

        return response

    def export_board_json(self, request, board_id):
        board = self.get_object(request, board_id)
        if not board:
            return JsonResponse({'error': 'Board not found'}, status=404)

        data = {
            'name': board.name,
            'created_at': board.created_at.isoformat(),
            'creator': board.creator.username,
            'items': [
                {
                    'text': item.text,
                    'suggested_by': item.suggested_by
                }
                for item in board.items.all()
            ]
        }

        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="bingo_board_{board.name}_{datetime.now().strftime("%Y%m%d")}.json"'
        return response


@admin.register(BingoGame)
class BingoGameAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'board', 'creator', 'created_at', 'is_active', 'player_count', 'has_winner')
    list_filter = ('is_active', 'created_at', 'has_free_square')
    list_editable = ('is_active',)
    search_fields = ('code', 'creator__username', 'board__name')
    readonly_fields = ('code',)
    
    def player_count(self, obj):
        return obj.players.count()
    player_count.short_description = 'Number of Players'
    
    def has_winner(self, obj):
        return bool(obj.winner)
    has_winner.boolean = True
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:game_id>/end/',
                self.admin_site.admin_view(self.end_game),
                name='bingo_game_end',
            ),
        ]
        return custom_urls + urls
    
    def end_game(self, request, game_id):
        game = get_object_or_404(BingoGame, id=game_id)
        game.is_active = False
        game.save()
        
        # Notify all players through WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'game_{game.id}',
            {
                'type': 'game_update',
                'message': 'Game ended by administrator'
            }
        )
        
        messages.success(request, f"Successfully ended game '{game.code}'")
        return HttpResponseRedirect(
            reverse('admin:bingo_bingogame_changelist')
        )

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'created_at', 'is_connected', 'has_won')
    list_filter = ('has_won', 'is_connected', 'created_at')
    search_fields = ('name', 'game__code')
    readonly_fields = ('covered_positions',)

