from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        labels = {'text': 'Текст',
                  'group': 'Группа', }
        help_texts = {'text': 'Введите текст',
                      'group': 'Укажите группу', }
        fields = ('text', 'group', 'image', )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
