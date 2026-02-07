from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.core.paginator import Paginator

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model
from django.contrib import messages

from django.db.models import Q
from django.utils.html import strip_tags
from django.template.loader import render_to_string
    
from .forms import  UserEditForm, ProfileEditForm
from .models import UserProfile
from commentslikes.models import  Comment, Vote


from commentslikes.utils import UsernameValidator
# Create your views here.

User = get_user_model()


def home_view(request):
    votes = Vote.objects.select_related(
        'user__profile',  
        'teacher', 
        'subject'
    ).order_by('-created_at')[:10]
    
    # Todos los comentarios principales
    comments_qs = Comment.objects.filter(
        parent__isnull=True,

    ).order_by('-created_at')
    
    paginator = Paginator(comments_qs, 10)
    page = paginator.page(1) 
    
    context = {
        'comments': page.object_list,   
        'page_obj': page,             
        'notifications': request.user.notifications.all() if request.user.is_authenticated else [],
        'votes': votes,
        'enable_polling': False,    
    }
    return render(request, 'home.html', context)


def profile_view(request, slug):
    user_profile = get_object_or_404(UserProfile.objects.select_related('user'), slug=slug)
    
    profile_user = user_profile.user 
    
    votes = Vote.objects.select_related(
        'user__profile',  
        'teacher', 
        'subject'
    ).order_by('-created_at')[:10]
    
    comments_qs = Comment.objects.filter(
        parent__isnull=True,
        user=profile_user
    ).order_by('-created_at')
    
    paginator = Paginator(comments_qs, 10)
    page = paginator.page(1)
    
    context = {
        "profile_user": profile_user,
        "user_profile": user_profile,
        'comments': page.object_list,
        'page_obj': page,
        'notifications': request.user.notifications.all() if request.user.is_authenticated else [],
        'votes': votes,
    }
    return render(request, 'profile/profile.html', context)


@login_required
def profile_edit_view(request):
    user = request.user
    user_profile, _ = UserProfile.objects.get_or_create(user=user)

    required_fields = ['bio', 'location', 'profile_picture']
    missing_fields = [field for field in required_fields if not getattr(user_profile, field)]
    show_required_warning = 'required_fields' in request.GET and bool(missing_fields)

    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=user)
        profile_form = ProfileEditForm(request.POST, request.FILES, instance=user_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()  # El procesamiento de imagen se hace dentro del save() del modelo

            # Mensajes según completitud
            if all(getattr(user_profile, field) for field in required_fields):
                messages.success(request, 'Perfil actualizado y completado correctamente')
                return redirect('home')
            else:
                messages.success(request, 'Perfil actualizado correctamente')
                return redirect('home')
        else:
            all_errors = user_form.errors.as_ul() + profile_form.errors.as_ul()
            all_errors_text = strip_tags(all_errors)
            messages.error(request, f'Por favor corrige los errores: {all_errors_text}')
    else:
        user_form = UserEditForm(instance=user)
        profile_form = ProfileEditForm(instance=user_profile)

    context = {
        'form': user_form,
        'profile_form': profile_form,
        'user_profile': user_profile,
        'missing_fields': missing_fields,
        'show_required_warning': show_required_warning,
    }

    return render(request, 'profile/profile_edit.html', context)

def confifraciones(request):
    return render(request,'conf/configuraciones.html')


def politicas(request):
    context = {
        'omitir_includes': True,  # Variable de control.
    }
    return render(request,'politicas/politicas.html', context)


@require_POST
def check_username(request):
    username = request.POST.get("username", "").strip()
    user_id = request.user.id if request.user.is_authenticated else None
    is_valid, message = UsernameValidator.validate_username(username, current_user_id=user_id)

    html = render_to_string("username_feedback.html", {
        "is_valid": is_valid,
        "message": message
    })
    return HttpResponse(html)



def tutoriales(request):
    steps = [
        {
            'title': "1️⃣ Configuración de Django",
            'description': "Configura SECRET_KEY, DEBUG, ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS usando variables de entorno.",
            'code': 'SECRET_KEY = os.getenv("SECRET_KEY", "valor_por_defecto")\nDEBUG = False\nALLOWED_HOSTS = ["localhost", "127.0.0.1", "miapp.up.railway.app"]\nCSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "https://miapp.up.railway.app"]'
        },
        {
            'title': "2️⃣ WhiteNoise y Tailwind",
            'description': "Sirve archivos estáticos con WhiteNoise y estiliza tu frontend con TailwindCSS.",
            'code': 'MIDDLEWARE = [\n    "django.middleware.security.SecurityMiddleware",\n"django.contrib.sessions.middleware.SessionMiddleware",\n"whitenoise.middleware.WhiteNoiseMiddleware",\n    ...\n]\n\nSTATIC_URL = "/static/"\nSTATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")\nSTATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"'
        },
        {
            'title': "3️⃣ Base de datos",
            'description': "Configura PostgreSQL en Railway y usa dj-database-url para producción.",
            'code': 'import dj_database_url\n\nif os.getenv("RAILWAY_ENVIRONMENT") == "production":\n    DATABASES = {\n"default": dj_database_url.config(conn_max_age=600, ssl_require=True)\n    }\nelse:\n    DATABASES = {\n        "default": {\n            "ENGINE": "django.db.backends.sqlite3",\n            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),\n        }\n    }'
        },
        {
            'title': "4️⃣ Despliegue con Gunicorn",
            'description': "Usa railway.json o Procfile para iniciar la app con Gunicorn.",
            'code': '# Procfile\nweb: gunicorn socialnetwork.wsgi:application --bind 0.0.0.0:$PORT\n\n# railway.json\n{\n  "deploy": {\n"startCommand": "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn socialnetwork.wsgi:application --bind 0.0.0.0:$PORT"\n  }\n}'
        },
        {
            'title': "5️⃣ Blog con Tailwind",
            'description': "Crea posts, lista principal y detalle de posts con estilo responsive usando Tailwind.",
            'code': 'from django.db import models\nfrom django.utils import timezone\nfrom django.urls import reverse\n\nclass Post(models.Model):\n    title = models.CharField(max_length=200)\n    content = models.TextField()\n    created_at = models.DateTimeField(default=timezone.now)\n    slug = models.SlugField(unique=True, max_length=200)\n\n    def get_absolute_url(self):\n        return reverse("post_detail", kwargs={"slug": self.slug})'
        },
    ]
    return render(request,'tutoriales/deploy.html',{"steps": steps})


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /private/",
        "Allow: /",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")



