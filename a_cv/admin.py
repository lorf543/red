from django.contrib import admin
from .models import (
    CVTemplate, CV, Experience, Education, 
    SkillCategory, Skill, Language, Certification
)

# ========== ADMIN PARA TEMPLATES ==========
@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'template_code', 'is_active', 'is_premium', 'order']
    list_filter = ['category', 'is_active', 'is_premium']
    search_fields = ['name', 'description', 'template_code']
    list_editable = ['is_active', 'is_premium', 'order']
    prepopulated_fields = {'template_code': ('name',)}
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'category')
        }),
        ('Configuración Técnica', {
            'fields': ('template_code', 'html_file')
        }),
        ('Visual', {
            'fields': ('preview_image',)
        }),
        ('Configuración', {
            'fields': ('is_active', 'is_premium', 'order')
        }),
    )


# ========== INLINES PARA CV ==========
class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1
    fields = ['position', 'company', 'location', 'start_date', 'end_date', 'current', 'responsibilities']

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1
    fields = ['institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'current']

class SkillCategoryInline(admin.TabularInline):
    model = SkillCategory
    extra = 1
    fields = ['name', 'order']

class LanguageInline(admin.TabularInline):
    model = Language
    extra = 1
    fields = ['language', 'proficiency']

class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 1
    fields = ['name', 'issuing_organization', 'issue_date', 'expiration_date']


# ========== ADMIN PARA CV ==========
@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'user', 'template', 'public', 'slug', 'created_at']
    list_filter = ['template', 'public', 'created_at']
    search_fields = ['full_name', 'user__username', 'user__email', 'slug']
    list_editable = ['public']
    list_per_page = 20
    prepopulated_fields = {'slug': ('full_name',)}
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'template')
        }),
        ('Información Personal', {
            'fields': ('full_name', 'email', 'phone', 'location', 'profile_photo')
        }),
        ('Enlaces', {
            'fields': ('website', 'linkedin', 'github')
        }),
        ('Resumen Profesional', {
            'fields': ('professional_summary',)
        }),
        ('Configuración', {
            'fields': ('public', 'slug')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [
        ExperienceInline,
        EducationInline,
        SkillCategoryInline,
        LanguageInline,
        CertificationInline,
    ]


# ========== ADMIN PARA MODELOS INDIVIDUALES ==========
@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ['cv', 'position', 'company', 'location', 'start_date', 'end_date', 'current']
    list_filter = ['current', 'company', 'start_date']
    search_fields = ['position', 'company', 'location', 'cv__full_name', 'cv__user__username']
    list_per_page = 20
    
    fieldsets = (
        ('CV', {
            'fields': ('cv',)
        }),
        ('Información del Puesto', {
            'fields': ('position', 'company', 'location')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date', 'current')
        }),
        ('Detalles', {
            'fields': ('responsibilities',)
        }),
    )


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['cv', 'degree', 'institution', 'field_of_study', 'start_date', 'end_date', 'current']
    list_filter = ['current', 'institution', 'start_date']
    search_fields = ['degree', 'institution', 'field_of_study', 'cv__full_name', 'cv__user__username']
    list_per_page = 20
    
    fieldsets = (
        ('CV', {
            'fields': ('cv',)
        }),
        ('Información Académica', {
            'fields': ('institution', 'degree', 'field_of_study')
        }),
        ('Fechas', {
            'fields': ('start_date', 'end_date', 'current')
        }),
        ('Descripción', {
            'fields': ('description',)
        }),
    )


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1
    fields = ['name', 'proficiency']


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'cv', 'order']
    search_fields = ['name', 'cv__full_name', 'cv__user__username']
    list_per_page = 20
    
    inlines = [SkillInline]
    
    fieldsets = (
        ('Información', {
            'fields': ('cv', 'name', 'order')
        }),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'proficiency']
    list_filter = ['proficiency', 'category']
    search_fields = ['name', 'category__name']
    list_per_page = 20
    
    fieldsets = (
        ('Información', {
            'fields': ('category', 'name', 'proficiency')
        }),
    )


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['language', 'proficiency', 'cv']
    list_filter = ['proficiency']
    search_fields = ['language', 'cv__full_name', 'cv__user__username']
    list_per_page = 20
    
    fieldsets = (
        ('Información', {
            'fields': ('cv', 'language', 'proficiency')
        }),
    )


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'issuing_organization', 'cv', 'issue_date', 'expiration_date']
    list_filter = ['issuing_organization', 'issue_date']
    search_fields = ['name', 'issuing_organization', 'cv__full_name', 'cv__user__username']
    list_per_page = 20
    
    fieldsets = (
        ('CV', {
            'fields': ('cv',)
        }),
        ('Información de Certificación', {
            'fields': ('name', 'issuing_organization')
        }),
        ('Fechas', {
            'fields': ('issue_date', 'expiration_date')
        }),
        ('Credenciales', {
            'fields': ('credential_id', 'credential_url'),
            'classes': ('collapse',)
        }),
    )