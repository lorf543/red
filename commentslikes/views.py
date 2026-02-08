from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST, require_GET
from django.template.loader import render_to_string
from django.db.models import Count, F, Q
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from jigsawstack import JigsawStack

import re

import threading
import cloudinary.uploader

from .utils  import contains_badwords, get_badwords_in_text, check_nsfw_cached
from .models import Comment, Reaction, Teacher



from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.utils.html import escape



ai = JigsawStack(api_key="sk_8fc49d46d26248a05274e78faf07893cffb62e8b25790d47e2b7ef4eca158b07ef7fbb73c69ef0e5514e8c2ac92ff956111ecbb0d7335d13cdcdb50a1525ddad024KIVF6vZqFa5acHSxde")


def validate_comment_image(comment_id):
    """Validar imagen en segundo plano"""
    try:
        comment = Comment.objects.get(id=comment_id)
        
        if not comment.image:
            return
    
        image_url = comment.image.url
        
        print(f"🔍 Validando imagen: {image_url}")
        
        # Validar con JigsawStack
        result = ai.validate.nsfw({"url": image_url})
        
        if result.get("nsfw"):
            comment.image_status = 'nsfw'
            cloudinary.uploader.destroy(comment.image.public_id)
            print(f"❌ Imagen NSFW detectada - Comentario {comment_id}")
        else:
            comment.image_status = 'safe'
            print(f"✅ Imagen segura - Comentario {comment_id}")
        
        comment.save(update_fields=['image_status'])
        
    except Comment.DoesNotExist:
        print(f"⚠️ Comentario {comment_id} no existe")
    except Exception as e:
        print(f"⚠️ Error validando imagen del comentario {comment_id}: {e}")
        # En caso de error, marcar como safe para no bloquear
        try:
            comment = Comment.objects.get(id=comment_id)
            comment.image_status = 'safe'
            comment.save(update_fields=['image_status'])
        except:
            pass


def get_comment_status(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.image_status != "pending":
        return render(
            request,
            'components/comment_content_fragment.html',
            {
                'comment': comment,
                'enable_polling': False
            }
        )

    return render(
        request,
        'components/comment_content_fragment.html',
        {
            'comment': comment,
            'enable_polling': True
        }
    )


@login_required
@require_POST
def create_comment(request):
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')

    # 1. Validación vacío
    if not content and not image:
        return error_hx_response("El comentario no puede estar vacío.")

    # 2. Badwords
    if content:
        badwords_found = get_badwords_in_text(content)
        if badwords_found:
            unique_words = ', '.join(sorted(set(badwords_found)))
            return error_hx_response(
                f'Palabras no permitidas: <strong class="text-red-600">{escape(unique_words)}</strong>.'
            )

    parent_id = request.POST.get('parent')
    parent_comment = Comment.objects.filter(pk=parent_id).first() if parent_id else None

    try:
        # Crear comentario
        comment = Comment.objects.create(
            user=request.user,
            content=content,
            parent=parent_comment,
            image=image,  
            image_status='pending' if image else None 
        )
        comment.process_mentions()

        # Si hay imagen, validar en segundo plano
        if image:
            threading.Thread(
                target=validate_comment_image,
                args=(comment.id,),  # Solo necesitas el ID
                daemon=True
            ).start()

        return render(request, 'components/comment_item.html', {'comment': comment,"enable_polling": True})

    except Exception as e:
        print(f"Error creando comentario: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponseServerError(
            f'<div class="text-red-600">Error: {str(e)}</div>'
        )


def error_hx_response(message):
    """Función auxiliar para errores HTMX"""
    response = HttpResponse(
        f'<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded-lg">{message}</div>'
    )
    response['HX-Retarget'] = '#commentErrorContainer'
    response['HX-Reswap'] = 'innerHTML'
    return response
    
@login_required
@require_POST
def create_teacher_comment(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')

    # 1. Validación vacío
    if not content and not image:
        return error_hx_response("El comentario no puede estar vacío.")

    # 2. Badwords
    if content:
        badwords_found = get_badwords_in_text(content)
        if badwords_found:
            unique_words = ', '.join(sorted(set(badwords_found)))
            return error_hx_response(
                f'Palabras no permitidas: <strong class="text-red-600">{escape(unique_words)}</strong>.'
            )

    parent_id = request.POST.get('parent')
    parent_comment = Comment.objects.filter(pk=parent_id).first() if parent_id else None

    try:
        # Crear comentario
        comment = Comment.objects.create(
            user=request.user,
            teacher=teacher,  # ¡IMPORTANTE! Falta esta línea
            content=content,
            parent=parent_comment,
            image=image,
            image_status='pending' if image else None
        )
        comment.process_mentions()

        # Si hay imagen, validar en segundo plano
        if image:
            threading.Thread(
                target=validate_comment_image,
                args=(comment.id,),  # Solo necesitas el ID
                daemon=True
            ).start()

        return render(request, 'components/comment_item.html', {'comment': comment,"enable_polling": True})

    except Exception as e:
        print(f"Error creando comentario: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponseServerError(
            f'<div class="text-red-600">Error: {str(e)}</div>'
        )

 
     
@login_required
@require_http_methods(["GET", "POST"])
def update_comment(request, comment_id):
    
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)

    if request.method == 'POST':

        content = request.POST.get('content', '').strip()
        
        badwords_found = get_badwords_in_text(content)
        if badwords_found:
            unique_words = sorted(set(badwords_found))
            badwords_list = ', '.join(unique_words)
            message = f'Tu comentario contiene las siguientes palabras no permitidas: <strong class="text-red-600">{escape(badwords_list)}</strong>. Por favor, modifícalo.'
            return HttpResponse(f'<p id="message">{message}</p>')
    
        if not content:
            messages.error(request, "El contenido no puede estar vacío")

        else:
            comment.content = content
            comment.save()
            if comment.content == None:
                return render(request, 'components/comment_item.html', {'comment': comment},)
            else:
                return render(request, 'components/reply_item.html', {'comment': comment})
    
    return render(request, 'components/comment_edit_form.html', {'comment': comment})

@login_required
def create_reply(request, comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id)
    content = request.POST.get('content', '').strip()

    if not content:
        return HttpResponseBadRequest("El contenido de la respuesta no puede estar vacío")
    
    badwords_found = get_badwords_in_text(content)
    if badwords_found:
        unique_words = sorted(set(badwords_found))
        badwords_list = ', '.join(unique_words)
        message = f'Tu comentario contiene las siguientes palabras no permitidas: <strong class="text-red-600">{escape(badwords_list)}</strong>. Por favor, modifícalo.'
        return HttpResponse(f'<p id="message">{message}</p>')

    try:
        # Heredamos el subject o teacher del comentario padre
        reply_data = {
            'user': request.user,
            'content': content,
            'parent': parent_comment
        }
        
        # Si el comentario padre tiene subject, lo heredamos
        if parent_comment.subject:
            reply_data['subject'] = parent_comment.subject
        # Si el comentario padre tiene teacher, lo heredamos
        elif parent_comment.teacher:
            reply_data['teacher'] = parent_comment.teacher
        
        reply = Comment.objects.create(**reply_data)
        
        return render(request, 'components/reply_item.html', {
            'comment': reply
        })

    except Exception as e:
        return HttpResponseServerError(str(e))


@login_required
@require_http_methods(["GET"])
def comment_detail_partial(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.parent == None:
        return render(request, 'components/comment_item.html', {'comment': comment})
    else:
        return render(request, 'components/reply_item.html', {'comment': comment})

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    comment.delete()
    return HttpResponse(status=204)


def load_more_replies(request, comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id)
    page_number = int(request.GET.get('page', 2))  # Convertir a int
    
    replies = parent_comment.replies.all().order_by('created_at')
    paginator = Paginator(replies, 3) 
    
    try:
        page = paginator.page(page_number)
        
        context = {
            'replies': page,
            'has_next': page.has_next(),
            'next_page': page_number + 1 if page.has_next() else None,
            'parent_comment': parent_comment,
        }
        
        return render(request, 'components/replies/replies_list.html', context)
        
    except EmptyPage:
        return HttpResponse('')

def load_more_comments(request):
    page_number = request.GET.get('page', 2)
    
    comments_qs = Comment.objects.filter(
        parent__isnull=True,
    ).order_by('-created_at')
    
    paginator = Paginator(comments_qs, 10) # Paginador de 2 para probar
    
    try:
        page_obj = paginator.page(page_number)
    except EmptyPage:
        # Si la página está vacía, devolvemos un div vacío con OOB para eliminar el botón
        return HttpResponse('<div id="load-more-comments-container" hx-swap-oob="true"></div>')
    except PageNotAnInteger:
        page_obj = paginator.page(2)

    context = {
        'comments': page_obj.object_list,
        'page_obj': page_obj
    }
    
    return render(request, 'components/comments/comments_list.html', context)

@require_POST
@login_required
def react_to_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    reaction_type = int(request.POST.get('reaction_type'))
    
    reaction, created = Reaction.objects.get_or_create(
        user=request.user,
        content_type=ContentType.objects.get_for_model(comment),
        object_id=comment.id,
        defaults={'reaction_type': reaction_type}
    )
    
    if not created:
        if reaction.reaction_type == reaction_type:
            reaction.delete()
        else:
            reaction.reaction_type = reaction_type
            reaction.save()
    
    # Vuelve a obtener el comentario actualizado para que los counts sean correctos
    comment.refresh_from_db()
    
    # Renderizar el template actualizado
    html = render_to_string('partials/reaction_buttons.html', {
        'comment': comment,
        'likes_count': comment.likes_count,
        'dislikes_count': comment.dislikes_count,
        'user_reaction': comment.user_reaction(request.user),
        'request': request,
        "user": request.user,
    })
    
    return HttpResponse(html)

def look_users(request):
    content = request.GET.get('content', '')
    match = re.search(r'@(\w+)$', content)
    if not match:
        return HttpResponse('')  # Vacío si no hay @

    query = match.group(1)
    users = User.objects.filter(username__icontains=query)[:15]

    if not users:
        return HttpResponse('')

    html = render_to_string('partials/mentions_list.html', {'users': users})
    return HttpResponse(html)

@login_required
@require_POST
def toggle_moderate(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Verificar permisos (opcional: solo staff o superusers pueden moderar)
    if not request.user.is_staff:
        return HttpResponseForbidden("No tienes permiso para moderar comentarios")
    
    comment.is_active = not comment.is_active
    comment.moderated_by = request.user
    comment.moderated_at = timezone.now()
    comment.save()
    
    return HttpResponse(
        '✅ Comentario moderado            <p> los cambios si estan pero tendra que darle f5, por que soy vago para hacer que sea dinamico</p>' if not comment.is_active else '👁️ Comentario visible'
    )
 
 
@require_GET
def get_comment_likes(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Obtener usuarios que dieron like
    likes = comment.reactions.filter(reaction_type=1).select_related('user')
    
    users = [{
        'id': like.user.id,
        'name': like.user.get_full_name() or like.user.username,
        'username': like.user.username,
    } for like in likes]
    
    return JsonResponse({'users': users}) 
     

def top_comments_view(request):
    top_comments = (
        Comment.objects
        .select_related('user', 'user__profile')
        .annotate(
            likes_count_db=Count('reactions', filter=Q(reactions__reaction_type=Reaction.LIKE), distinct=True),
            replies_count_db=Count('replies', distinct=True)
        )
        .annotate(score=F('likes_count_db') + F('replies_count_db'))
        .order_by('-score', '-created_at')[:3]
    )

    return render(request, 'components/top_comments.html', {
        'comments': top_comments
    })