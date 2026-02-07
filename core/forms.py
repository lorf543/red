# forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import UserProfile
from datetime import date
import re
from commentslikes.utils import UsernameValidator
from allauth.account.forms import LoginForm, SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].label = 'Nombre de usuario'
        if 'placeholder' in self.fields['password'].widget.attrs:
            del self.fields['password'].widget.attrs['placeholder']
        if 'placeholder' in self.fields['login'].widget.attrs:
            del self.fields['login'].widget.attrs['placeholder']


class CustomSignupForm(SignupForm):
    # Asegurarnos de que el campo username existe
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Asegurar que el campo username existe
        if 'username' not in self.fields:
            self.fields['username'] = forms.CharField(
                label=_('Nombre de usuario'),
                max_length=150,
                required=True,
                help_text=_('No puede contener términos administrativos')
            )
        
        # Configurar campos
        self.fields['username'].label = _('Nombre de usuario')
        self.fields['username'].help_text = _('No puede contener términos administrativos')
        
        # Hacer el email opcional para registro tradicional
        if 'email' in self.fields:
            self.fields['email'].required = False
            self.fields['email'].label = _('Correo electrónico (opcional)')
        
        # Remover placeholders y agregar clases
        for field in ['password1', 'password2']:
            if field in self.fields:
                if 'placeholder' in self.fields[field].widget.attrs:
                    del self.fields[field].widget.attrs['placeholder']
                self.fields[field].widget.attrs['class'] = 'password-field'
        
        # Si el email no es requerido, mostrar mensaje claro
        if 'email' in self.fields and not self.fields['email'].required:
            self.fields['email'].help_text = _('Recomendado para recuperar tu cuenta')

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if username:  # Solo validar si hay username
            is_valid, message = UsernameValidator.validate_username(username)
            if not is_valid:
                raise ValidationError(message)
        return username

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        username = cleaned_data.get('username', '')
        
        # Si no hay username, generar uno basado en email o aleatorio
        if not username and 'username' in self.fields:
            if email:
                # Usar parte del email antes del @ como username
                username = email.split('@')[0]
            else:
                # Generar username aleatorio
                import random
                import string
                username = 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            
            # Asegurar que el username sea único
            from django.contrib.auth.models import User
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            
            cleaned_data['username'] = username
        
        # Si el usuario se registra sin email, generar uno temporal
        if not email and 'email' in self.fields:
            # Generar un email temporal único
            cleaned_data['email'] = f"{username}@temp.noemail"
        
        return cleaned_data
    
    def save(self, request):
        # Asegurar que el username esté en cleaned_data
        if 'username' not in self.cleaned_data:
            self.cleaned_data['username'] = self.generate_username()
        
        user = super().save(request)
        return user
    
    def generate_username(self):
        """Generar un username único si no se proporcionó"""
        import random
        import string
        from django.contrib.auth.models import User
        
        while True:
            username = 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            if not User.objects.filter(username=username).exists():
                return username


class CustomSocialSignupForm(SocialSignupForm):
    username = forms.CharField(
        label=_('Nombre de usuario'),
        max_length=150,
        required=True,
        help_text=_('Elige un nombre de usuario único')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si el usuario viene de Google, el email ya está verificado
        # Podemos ocultar el campo email si ya viene de Google
        sociallogin = kwargs.get('sociallogin')
        if sociallogin and sociallogin.account.provider == 'google':
            if 'email' in self.fields:
                self.fields['email'].widget.attrs['readonly'] = True
                self.fields['email'].help_text = _('Email verificado por Google')
    
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if username:
            is_valid, message = UsernameValidator.validate_username(username)
            if not is_valid:
                raise ValidationError(message)
        return username
    
    def save(self, request):
        # Guardar el usuario
        user = super().save(request)
        
        # Si viene de Google, podemos marcar el email como verificado
        sociallogin = self.sociallogin
        if sociallogin and sociallogin.account.provider == 'google':
            if user.email and not user.email.endswith('@temp.noemail'):
                from allauth.account.models import EmailAddress
                EmailAddress.objects.add_email(
                    request, user, user.email, confirm=False
                )
        
        return user


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si el usuario tiene email temporal (de registro sin email),
        # mostrar campo vacío
        if self.instance.email and self.instance.email.endswith('@temp.noemail'):
            self.fields['email'].initial = ''
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Evitar emails temporales
        if email and email.endswith('@temp.noemail'):
            raise ValidationError(_('Por favor ingresa un email válido'))
        
        return email


class UserEditForm(UserChangeForm):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-input mt-1 block w-full rounded-md border-gray-300 shadow-sm'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'pattern': '.*[A-Za-z].*',
                'title': 'El nombre de usuario debe contener al menos una letra'
            }),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            self.fields.pop('password')  # Eliminamos el campo de password
    
    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()

        # Si no cambió el username, omitir validación completa
        if username.lower() == self.instance.username.lower():
            return username

        user_id = self.instance.pk

        is_valid, message = UsernameValidator.validate_username(username, current_user_id=user_id)

        if not is_valid:
            raise ValidationError(message)

        return username


LOCATION_CHOICES = [
    ('santo_domingo', 'Santo Domingo'),
    ('santiago', 'Santiago de los Caballeros'),
    ('la_romana', 'La Romana'),
    ('san_pedro_de_macoris', 'San Pedro de Macorís'),
    ('puerto_plata', 'Puerto Plata'),
    ('moca', 'Moca'),
    ('san_francisco_de_macoris', 'San Francisco de Macorís'),
    ('bani', 'Bani'),
    ('higuey', 'Higuey'),
    ('barahona', 'Barahona'),
    ('san_cristobal', 'San Cristóbal'),
    ('la_vega', 'La Vega'),
    ('monte_cristi', 'Monte Cristi'),
    ('dajabon', 'Dajabón'),
    ('azua', 'Azua'),
    ('el_seibo', 'El Seibo'),
    ('samana', 'Samaná'),
    ('valverde', 'Valverde'),
    ('san_jose_de_ocoa', 'San José de Ocoa'),
    ('san_juan_de_la_maguana', 'San Juan de la Maguana'),
    ('pedernales', 'Pedernales'),
    ('constanza', 'Constanza'),
    ('jarabacoa', 'Jarabacoa'),
    ('nagua', 'Nagua'),
    ('bonao', 'Bonao'),
    ('los_alcarrizos', 'Los Alcarrizos'),
    ('villa_altagracia', 'Villa Altagracia'),
    ('santo_domingo_este', 'Santo Domingo Este'),
    ('santo_domingo_norte', 'Santo Domingo Norte'),
    ('santo_domingo_oeste', 'Santo Domingo Oeste'),
]


class ProfileEditForm(forms.ModelForm):
    location = forms.ChoiceField(
        choices=LOCATION_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-input',
            'placeholder': _('Ciudad, País')
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ('profile_picture', 'bio', 'location', 'birth_date')

        widgets = {
            'profile_picture': forms.ClearableFileInput(
                attrs={
                    'style': 'font-size:13px',
                    'accept': 'image/png, image/jpeg',
                }
            ),
            'bio': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': _('Cuéntanos algo sobre ti'),
                'maxlength': '250',
            }),
            'birth_date': forms.DateInput(attrs={
                'style': 'cursor:pointer;',
                'type': 'date',
                'onkeydown': 'return false',
                'min': '1980-12-31',
                'max': '2015-12-31',
            }),
        }
        labels = {
            'profile_picture': _('Foto de perfil'),
            'bio': _('Biografía'),
            'location': _('Ubicación'),
            'birth_date': _('Fecha de nacimiento'),
        }
    
    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '')
        if len(bio) > 250:
            raise ValidationError(_('La biografía no puede exceder los 250 caracteres.'))
        return bio
    
    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 13:
                raise ValidationError(_('Debes tener al menos 13 años para registrarte.'))
            
            if age > 120:
                raise ValidationError(_('Por favor ingresa una fecha de nacimiento válida.'))
        
        return birth_date