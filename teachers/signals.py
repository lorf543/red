from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


from schedules.models import Teacher
from commentslikes.models import Vote

@receiver([post_save, post_delete], sender=Teacher)
@receiver([post_save, post_delete], sender=Vote)
def invalidate_teachers_cache(sender, **kwargs):
    cache.clear()
    
    
@receiver([post_save, post_delete], sender=Teacher)
def invalidate_teacher_cache_on_teacher_change(sender, instance, **kwargs):
    invalidate_teachers_cache()
    print(f"🔄 Caché invalidado por cambio en Teacher: {instance.full_name}")


@receiver([post_save, post_delete], sender=Vote)
def invalidate_teacher_cache_on_vote_change(sender, instance, **kwargs):
    invalidate_teachers_cache()
    target = instance.teacher or instance.subject
    print(f"🔄 Caché invalidado por voto a: {target}")


def invalidate_teachers_cache():
    """
    Función helper para invalidar el caché de teachers.
    """
    # Opción 1: Si usas django-redis, puedes borrar por patrón
    # try:
    #     cache.delete_pattern("teachers_list_*")
    # except AttributeError:
        # Opción 2: Si usas caché por defecto de Django (sin redis)
        # Borrar claves conocidas manualmente
    # cache_keys = [
    #     'teachers_list_main',
    #     'teachers_stats',
    # ]
    # cache.delete_many(cache_keys)
        
        # O simplemente limpiar todo el caché (drástico pero efectivo)
    cache.clear()
    
    
@receiver([post_save, post_delete], sender=Vote)
def invalidate_votes_cache(sender, instance, **kwargs):
    cache.delete('votes_stats_v1')

    try:
        cache.delete_pattern("teachers_list_*")
    except AttributeError:

        cache.delete("teachers_list_main")
    
    target = instance.teacher or instance.subject
    print(f"🔄 Caché de votos invalidado por voto a: {target}")