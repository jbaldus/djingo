# bingo/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory
from .models import BingoBoard, BingoBoardItem, BingoGame

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class PlayerNameForm(forms.Form):
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your name'
        })
    )


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

class CreateGameForm(forms.ModelForm):
    class Meta:
        model = BingoGame
        fields = ['board', 'has_free_square', 'board_size', 'win_condition']
        widgets = {
            'board_size': forms.RadioSelect,
            'win_condition': forms.RadioSelect,
        }