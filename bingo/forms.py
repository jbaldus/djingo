# bingo/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.safestring import mark_safe
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from crispy_forms.bootstrap import FieldWithButtons, StrictButton
from .models import BingoBoard, BingoBoardItem, BingoGame, Feedback
from .utils import generate_silly_nickname

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'message', 'game_code', 'game_name']
        widgets = {
            'game_code': forms.HiddenInput(),
            'game_name': forms.HiddenInput(),
        }


class PlayerNameForm(forms.Form):
    nickname = forms.CharField(label="Silly Nickname",
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            # 'placeholder': 'Enter your first name or a silly nickname'
        }),
        help_text="Just put your first name or a nickname -- we're not trying to steal any identities here 😉. This will be displayed on other players games when you mark a bingo square."
    )
    
    use_suggested_items = forms.BooleanField(
        label="Show user submitted suggestions",
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        self.game = kwargs.pop("game", None)
        super().__init__(*args, **kwargs)
        # if not kwargs.get("initial", None):
        self.fields["nickname"].initial = generate_silly_nickname(game=self.game)
        self.fields["nickname"].widget.attrs['placeholder'] = self.fields["nickname"].initial

        self.helper = FormHelper()
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            FieldWithButtons(
                "nickname",
                StrictButton(
                    mark_safe('<i class="bi bi-shuffle"></i>'),
                    css_class="gb-btn btn btn-secondary",
                    css_id="randomize-btn",
                    type="button",
                ),
            ),
            # list other fields normally so crispy renders them after nickname
            "use_suggested_items",
            # ...
            Submit("submit", "Start Playing", css_class="gb-is-big btn btn-primary"),
        )

class PlayerNameChangeForm(forms.Form):
    nickname = forms.CharField(label="Silly Nickname:",
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name or a silly nickname'
        }),
        help_text="Just put your first name or a nickname -- we're not trying to steal any identities here 😉. This will be displayed on other players games when you mark a bingo square."
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
        fields = ['name', 'board', 'has_free_square', 'board_size', 'win_condition']
        widgets = {
            'board_size': forms.RadioSelect,
            'win_condition': forms.RadioSelect,
        }

class SuggestionForm(forms.Form):
    suggestion1 = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control suggestion-input',
            'placeholder': 'Suggestion 1',
            'maxlength': 64,
        })
    )
    suggestion2 = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control suggestion-input',
            'placeholder': 'Suggestion 2',
            'maxlength': 64,
        })
    )
    suggestion3 = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control suggestion-input',
            'placeholder': 'Suggestion 3',
            'maxlength': 64,
        })
    )