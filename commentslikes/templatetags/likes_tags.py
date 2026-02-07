from django import template
from django.contrib.contenttypes.models import ContentType
from commentslikes.models import Reaction  

register = template.Library()

@register.filter
def content_type_id(obj):
    """Obtiene el ID del ContentType para el modelo del objeto"""
    ct = ContentType.objects.get_for_model(obj)
    return ct.id

@register.filter
def user_reaction(obj, user):
    """Obtiene la reacción del usuario actual al objeto"""
    if not user.is_authenticated:
        return None
    
    ct = ContentType.objects.get_for_model(obj)
    try:
        reaction = Reaction.objects.get(
            user=user,
            content_type=ct,
            object_id=obj.id
        )
        return reaction.reaction_type
    except Reaction.DoesNotExist:
        return None

@register.filter
def likes_count(obj):
    """Cuenta los likes para un objeto"""
    ct = ContentType.objects.get_for_model(obj)
    return Reaction.objects.filter(
        content_type=ct,
        object_id=obj.id,
        reaction_type=Reaction.LIKE
    ).count()

@register.filter
def dislikes_count(obj):
    """Cuenta los dislikes para un objeto"""
    ct = ContentType.objects.get_for_model(obj)
    return Reaction.objects.filter(
        content_type=ct,
        object_id=obj.id,
        reaction_type=Reaction.DISLIKE
    ).count()
    
    
    
    
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)