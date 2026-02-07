from django import forms
from commentslikes.models import Comment



class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        labels = {
                'content': '',
            }
        exclude = ('teacher',)
        fields = ['content'] 
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6',
                'placeholder': 'Escribe tu comentario...'
            }),
        }
    
    

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Escribe tu respuesta...'
            }),
            'user_name': forms.TextInput(attrs={
                'class': 'form-control'
            })
        }
    