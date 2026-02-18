# forms.py
from django import forms
from .models import Experience, Education, SkillCategory, Skill, Language, Certification

class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['position', 'company', 'location', 'start_date', 'end_date', 'current', 'responsibilities']
        widgets = {
            'position': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Desarrollador Senior'}),
            'company': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Empresa XYZ'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Santo Domingo'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500'}),
            'current': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
            'responsibilities': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Describe tus responsabilidades...'}),
        }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['institution', 'degree', 'field_of_study', 'description', 'start_date', 'end_date', 'current']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Universidad Autónoma'}),
            'degree': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Licenciatura en Informática'}),
            'field_of_study': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Ciencias de la Computación'}),
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Descripción adicional...'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500'}),
            'current': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-blue-600 focus:ring-blue-500'}),
        }

class SkillCategoryForm(forms.ModelForm):
    class Meta:
        model = SkillCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Lenguajes de Programación'}),
        }

class SkillForm(forms.ModelForm):
    PROFICIENCY_CHOICES = [
        ('1', 'Básico'),
        ('2', 'Intermedio'),
        ('3', 'Avanzado'),
        ('4', 'Experto'),
    ]
    proficiency = forms.ChoiceField(choices=PROFICIENCY_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500'}))
    class Meta:
        model = Skill
        fields = ['name', 'proficiency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'flex-1 px-3 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Python'}),
        }

class LanguageForm(forms.ModelForm):
    PROFICIENCY_CHOICES = [
        ('basic', 'Básico'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
        ('native', 'Nativo'),
    ]
    proficiency = forms.ChoiceField(choices=PROFICIENCY_CHOICES, required=True,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500'}))
    class Meta:
        model = Language
        fields = ['language', 'proficiency']
        widgets = {
            'language': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Inglés'}),
        }

class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Certified Kubernetes Administrator'}),
            'issuing_organization': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: Cloud Native Computing Foundation'}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500'}),
            'credential_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'Ej: CKA-2024-12345'}),
            'credential_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500', 'placeholder': 'https://www.credential.net/12345'}),
        }