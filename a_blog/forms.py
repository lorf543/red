from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import BlogPost, PostSection
import bleach




class BlogPostForm(forms.ModelForm):
    main_paragraph = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = BlogPost
        fields = [
            "title",
            "subtitle",
            "main_paragraph",
            "main_image",
            "tags",
        ]
        widgets = {
            "tags": forms.CheckboxSelectMultiple(),
        }

        def clean_main_paragraph(self):
                return bleach.clean(
                    self.cleaned_data["main_paragraph"],
                    tags=[
                        'p', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'br'
                    ],
                    attributes={
                        # Permitimos el atributo 'style' en todas las etiquetas
                        '*': ['style'], 
                    },
                    styles=[ 
                        # Solo permitimos text-align. Bleach borrará cualquier otro estilo.
                        'text-align' 
                    ],
                    strip=True
                )

class PostSectionForm(forms.ModelForm):
    class Meta:
        model = PostSection
        fields = [
            "subtitle",
            "content",
            "order",
        ]
        widgets = {
            "content": CKEditorWidget(attrs={"rows": 10}),
        }

        def clean_main_paragraph(self):
                return bleach.clean(
                    self.cleaned_data["content"],
                    tags=[
                        'p', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'br'
                    ],
                    attributes={
                        # Permitimos el atributo 'style' en todas las etiquetas
                        '*': ['style'], 
                    },
                    styles=[ 
                        # Solo permitimos text-align. Bleach borrará cualquier otro estilo.
                        'text-align' 
                    ],
                    strip=True
                )