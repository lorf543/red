from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


from schedules.models import Teacher
from commentslikes.models import Vote, Comment

@receiver([post_save, post_delete], sender=Teacher)
@receiver([post_save, post_delete], sender=Vote)

def invalidate_teachers_cache(sender, **kwargs):
    cache.clear()
    

@receiver([post_save, post_delete], sender=Comment)
def invalidate_comments_cache(sender, instance, **kwargs):
    cache.delete("home:comments:page:*")
    print(f"🔄 Caché de comentarios invalidado por cambio en Comment ID: {instance.id}")   


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
    cache.clear()
    
    
@receiver([post_save, post_delete], sender=Vote)
def invalidate_votes_cache(sender, instance, **kwargs):
    cache.delete("home:votes:latest")
    cache.incr("votes:stats:version")
    cache.delete("votes_stats_v1")
    print(f"🔄 Caché de votos invalidado por cambio en Vote ID: {instance.id}")   