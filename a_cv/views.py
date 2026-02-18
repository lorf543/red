from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import (
    CVTemplate, CV, Experience, Education, 
    SkillCategory, Skill, Language, Certification
)

from .forms import ExperienceForm, EducationForm, SkillCategoryForm, SkillForm, LanguageForm, CertificationForm
import random
import re


# ========== GALERÍA DE TEMPLATES ==========
def cv_template_gallery(request):
    templates = CVTemplate.objects.filter(is_active=True)
    print(templates)
    
    # Si el usuario no es premium, solo mostrar templates gratuitos
    if not request.user.is_authenticated or not hasattr(request.user, 'profile') or not request.user.profile.is_premium:
        templates = templates.filter(is_premium=False)
    
    context = {
        'templates': templates,
    }
    return render(request, 'a_cv/template_gallery.html', context)


def preview_template(request, template_id):
    template = get_object_or_404(CVTemplate, id=template_id)

    # Obtener un CV real del usuario
    cv = CV.objects.filter(user=request.user).first()
    print(cv)

    if not cv:
        return redirect("create_cv", template_id=template.id)

    return render(request, template.html_file, {
        "cv": cv,
        "is_preview": True,
    })


# ========== CREAR CV ==========
@login_required
def create_cv(request, template_id):
    template = get_object_or_404(CVTemplate, id=template_id, is_active=True)
    
    # Verificar si es premium y el usuario tiene acceso
    if template.is_premium and (not hasattr(request.user, 'profile') or not request.user.profile.is_premium):
        messages.error(request, "Este template es premium. Actualiza tu cuenta para usarlo.")
        return redirect('cv_template_gallery')
    
    if request.method == 'POST':
        # Crear el CV
        cv = CV.objects.create(
            user=request.user,
            template=template,
            full_name=request.POST.get('full_name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            location=request.POST.get('location', ''),
            website=request.POST.get('website', ''),
            linkedin=request.POST.get('linkedin', ''),
            github=request.POST.get('github', ''),
            professional_summary=request.POST.get('professional_summary', ''),
            public=request.POST.get('public') == 'on',
        )
        
        # Guardar foto de perfil si existe
        if request.FILES.get('profile_photo'):
            cv.profile_photo = request.FILES['profile_photo']
            cv.save()
        
        # Guardar secciones relacionadas
        _save_experiences(request, cv)
        _save_education(request, cv)
        _save_skills(request, cv)
        _save_languages(request, cv)
        _save_certifications(request, cv)
        
        messages.success(request, "¡CV creado exitosamente!")
        return redirect('cv_detail', slug=cv.slug)
    
    context = {
        'template': template,
    }
    return render(request, 'a_cv/create_cv.html', context)


    # ========== FUNCIONES AUXILIARES PARA GUARDAR DATOS ==========


def _save_experiences(request, cv):
    """Guardar experiencias laborales"""
    experience_data = {}
    
    for key, value in request.POST.items():
        if key.startswith('experiences['):
            match = re.match(r'experiences\[(\d+)\]\[(\w+)\]', key)
            if match:
                index, field = match.groups()
                if index not in experience_data:
                    experience_data[index] = {}
                experience_data[index][field] = value
    
    for index, data in experience_data.items():
        if data.get('position') and data.get('company'):
            Experience.objects.create(
                cv=cv,
                position=data.get('position', ''),
                company=data.get('company', ''),
                location=data.get('location', ''),
                start_date=data.get('start_date'),
                end_date=data.get('end_date') if not data.get('current') else None,
                current=data.get('current') == 'on',
                responsibilities=data.get('responsibilities', '')
            )


def _save_education(request, cv):
    """Guardar educación"""
    education_data = {}
    
    for key, value in request.POST.items():
        if key.startswith('education['):
            match = re.match(r'education\[(\d+)\]\[(\w+)\]', key)
            if match:
                index, field = match.groups()
                if index not in education_data:
                    education_data[index] = {}
                education_data[index][field] = value
    
    for index, data in education_data.items():
        if data.get('institution') and data.get('degree'):
            Education.objects.create(
                cv=cv,
                institution=data.get('institution', ''),
                degree=data.get('degree', ''),
                field_of_study=data.get('field_of_study', ''),
                description=data.get('description', ''),
                start_date=data.get('start_date'),
                end_date=data.get('end_date') if not data.get('current') else None,
                current=data.get('current') == 'on'
            )

@require_POST
def add_skill_form(request):
    """Devuelve un formulario vacío de skill"""
    category_index = request.POST.get('category_index')
    if not category_index:
        return HttpResponse("Error: category_index es requerido", status=400)
    
    skill_index = random.randint(1000, 9999)
    form = SkillForm(prefix=f'skill_{category_index}_{skill_index}')
    
    return render(request, 'a_cv/partials/skill_form.html', {
        'form': form,
        'category_index': category_index,
        'skill_index': skill_index
    })


def _save_skills(request, cv):

    # Diccionario para agrupar datos por categoría
    categories_data = {}
    skills_data = {}
    
    # Recolectar todos los datos del POST
    for key, value in request.POST.items():
        # Formato: category_1234-name
        if key.startswith('category_') and '-name' in key:
            # Extraer el índice: "category_1234-name" -> "1234"
            prefix = key.split('-')[0]  # "category_1234"
            index = prefix.replace('category_', '')  # "1234"
            categories_data[index] = {'prefix': prefix}
        
        # Formato: skill_1234_5678-name o skill_1234_5678-proficiency
        elif key.startswith('skill_'):
            # "skill_1234_5678-name" -> ["skill", "1234", "5678-name"]
            parts = key.split('_')
            if len(parts) >= 3:
                category_idx = parts[1]  # "1234"
                skill_prefix = f"skill_{parts[1]}_{parts[2].split('-')[0]}"  # "skill_1234_5678"
                
                if category_idx not in skills_data:
                    skills_data[category_idx] = {}
                if skill_prefix not in skills_data[category_idx]:
                    skills_data[category_idx][skill_prefix] = {'prefix': skill_prefix}
    
    # Crear y validar categorías
    for index, cat_data in categories_data.items():
        form = SkillCategoryForm(request.POST, prefix=cat_data['prefix'])
        
        if form.is_valid():
            # Crear la categoría
            category = form.save(commit=False)
            category.cv = cv
            category.order = int(index)
            category.save()
            
            # Procesar skills de esta categoría
            if index in skills_data:
                for skill_prefix, skill_info in skills_data[index].items():
                    skill_form = SkillForm(request.POST, prefix=skill_prefix)
                    
                    if skill_form.is_valid():
                        skill = skill_form.save(commit=False)
                        skill.category = category
                        skill.save()


def _save_languages(request, cv):
    """Guardar idiomas"""
    language_data = {}
    
    for key, value in request.POST.items():
        if key.startswith('languages['):
            match = re.match(r'languages\[(\d+)\]\[(\w+)\]', key)
            if match:
                index, field = match.groups()
                if index not in language_data:
                    language_data[index] = {}
                language_data[index][field] = value
    
    for index, data in language_data.items():
        language_name = data.get('language')
        if language_name:
            Language.objects.create(
                cv=cv, 
                language=language_name,
                proficiency=data.get('proficiency', 'intermediate')
            )


def _save_certifications(request, cv):
    """Guardar certificaciones"""
    cert_data = {}
    
    for key, value in request.POST.items():
        if key.startswith('certifications['):
            match = re.match(r'certifications\[(\d+)\]\[(\w+)\]', key)
            if match:
                index, field = match.groups()
                if index not in cert_data:
                    cert_data[index] = {}
                cert_data[index][field] = value
    
    for index, data in cert_data.items():
        if data.get('name') and data.get('issuing_organization'):
            Certification.objects.create(
                cv=cv,
                name=data.get('name', ''),
                issuing_organization=data.get('issuing_organization', ''),
                issue_date=data.get('issue_date'),
                expiration_date=data.get('expiration_date') or None,
                credential_id=data.get('credential_id', ''),
                credential_url=data.get('credential_url', '')
            )


# ========== ENDPOINTS HTMX ==========
@require_POST
def add_experience(request):
    index = random.randint(1000, 9999)
    form = ExperienceForm(prefix=f'experience_{index}')
    return render(request, 'a_cv/partials/experience_form.html', {'form': form, 'index': index})

@require_POST
def add_education(request):
    index = random.randint(1000, 9999)
    form = EducationForm(prefix=f'education_{index}')
    return render(request, 'a_cv/partials/education_form.html', {'form': form, 'index': index})

@require_POST
def add_category(request):
    index = random.randint(1000, 9999)
    form = SkillCategoryForm(prefix=f'category_{index}')
    return render(request, 'a_cv/partials/category_form.html', {'form': form, 'index': index})

@require_POST
def add_skill(request):
    category_index = request.POST.get('category_index')
    if not category_index:
        return HttpResponse("Error: category_index requerido", status=400)
    skill_index = random.randint(1000, 9999)
    form = SkillForm(prefix=f'skill_{category_index}_{skill_index}')
    return render(request, 'a_cv/partials/skill_form.html', {'form': form, 'category_index': category_index, 'skill_index': skill_index})

@require_POST
def add_language(request):
    index = random.randint(1000, 9999)
    form = LanguageForm(prefix=f'language_{index}')
    return render(request, 'a_cv/partials/language_form.html', {'form': form, 'index': index})

@require_POST
def add_certification(request):
    index = random.randint(1000, 9999)
    form = CertificationForm(prefix=f'certification_{index}')
    return render(request, 'a_cv/partials/certification_form.html', {'form': form, 'index': index})
    section_index = random.randint(1000, 9999)
    return render(request, 'a_cv/partials/certification_form.html', {
        'index': section_index
    })


# ========== VISTA DE DETALLE (OPCIONAL) ==========
def cv_detail(request, slug):
    """Vista pública del CV"""
    cv = get_object_or_404(CV, slug=slug)
    
    # Solo mostrar si es público o es el dueño
    if not cv.public and (not request.user.is_authenticated or request.user != cv.user):
        messages.error(request, "Este CV no está disponible públicamente.")
        return redirect('home')
    
    context = {
        'cv': cv,
    }
    
    # Seleccionar template basado en el template del CV
    if cv.template.html_file:
        template_file = cv.template.html_file
    else:
        # Template por defecto
        template_file = 'a_cv/cv_templates/professional.html'
    
    return render(request, template_file, context)


