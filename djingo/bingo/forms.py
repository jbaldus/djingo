# bingo/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import BingoBoard, BingoBoardItem

class BingoBoardForm(forms.ModelForm):
    class Meta:
        model = BingoBoard
        fields = ['name']

BingoBoardItemFormSet = inlineformset_factory(
    BingoBoard,
    BingoBoardItem,
    fields=['text', 'position'],
    extra=25,
    min_num=25,
    validate_min=True,
    can_delete=True
)