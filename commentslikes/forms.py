from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content','image']  
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full border border-gray-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '¿Qué estás pensando?'
            })
        }