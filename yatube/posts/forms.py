from django import forms

from . import models
from .validators import validate_not_empty


class PostForm(forms.ModelForm):
    text = forms.CharField(
        label='Текст поста',
        widget=forms.Textarea,
        validators=[validate_not_empty]
    )

    group = forms.ModelChoiceField(
        label='Сообщество',
        queryset=models.Group.objects.all(),
        widget=forms.Select,
        empty_label='',
        required=False
    )

    class Meta:
        model = models.Post
        fields = ['text', 'group', 'image']


class CommentForm(forms.ModelForm):
    text = forms.CharField(
        label='Текст поста',
        widget=forms.Textarea,
        validators=[validate_not_empty]
    )

    class Meta:
        model = models.Comment
        fields = ['text']
