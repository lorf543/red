from django import forms
from django.core.exceptions import ValidationError
from schedules.models import Subject



class SubjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Estilos base para todos los campos
        base_style = 'w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500'
        
        # Aplicar estilos a cada campo
        self.fields['name'].widget.attrs.update({
            'class': f'{base_style}',
            'placeholder': 'Nombre de la materia'
        })
        
        self.fields['credits'].widget.attrs.update({
            'class': f'{base_style}',
            'min': '1',
            'max': '5'
        })
        
        self.fields['modalidad'].widget.attrs.update({
            'class': f'{base_style}'
        })
        
        self.fields['day'].widget.attrs.update({
            'class': f'{base_style}'
        })
        
        self.fields['hour'].widget.attrs.update({
            'class': f'{base_style}'
        })
        
        self.fields['teacher'].widget.attrs.update({
            'class': f'{base_style}'
        })
        
        # Campos requeridos
        self.fields['name'].required = True
        
        # Etiquetas personalizadas
        self.fields['modalidad'].label = "Modalidad de enseñanza"
        self.fields['day'].label = "Día de la semana"
        self.fields['hour'].label = "Hora de clase"
        self.fields['teacher'].label = "Profesor asignado"

    def clean_credits(self):
        credits = self.cleaned_data.get('credits')
        if credits is not None:
            if credits < 1:
                raise ValidationError("Los créditos no pueden ser menores a 1")
            if credits > 5:
                raise ValidationError("El máximo de créditos permitidos es 5")
        return credits

    
    class Meta:
        model = Subject
        fields = "__all__"
        exclude = ['description']
        widgets = {
            'modalidad': forms.Select(choices=Subject.MODALIDAD),
            'day': forms.Select(choices=Subject.DAYS_OF_WEEK),
            'hour': forms.Select(choices=Subject.HOURS_CHOICES),
        }
        labels = {
            'name': 'Nombre de la Materia',
            'credits': 'Créditos',
        }
        help_texts = {
            'credits': 'Número de créditos (1-5)',
        }


class CommentForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Escribe tu comentario...'
        }),
        max_length=1000,
        error_messages={
            'required': 'El contenido del comentario es obligatorio',
            'max_length': 'El comentario no puede exceder los 1000 caracteres'
        }
    )
    parent_id = forms.IntegerField(required=False, widget=forms.HiddenInput())