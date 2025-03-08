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
        }),
        help_text="Just put your first name or a nickname -- we're not trying to steal any identities here 😉. This will be displayed on other players games when you mark a bingo square."
    )
    
    use_suggested_items = forms.BooleanField(
        label="Show user submitted suggestions",
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class BingoBoardForm(forms.ModelForm):
    class Meta:
        model = BingoBoard
        fields = ['name']

BingoBoardItemFormSet = inlineformset_factory(
    BingoBoard,
    BingoBoardItem,
    fields=['text', 'suggested_by'],
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

class SuggestionForm(forms.Form):
    suggestion1 = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Suggestion 1',
            'maxlength': 64,
            'size': 64,
        })
    )
    suggestion2 = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Suggestion 2',
            'maxlength': 64,
            'size': 64,
        })
    )
    suggestion3 = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Suggestion 3',
            'maxlength': 64,
            'size': 64,
        })
    )