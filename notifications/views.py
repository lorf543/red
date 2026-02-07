from django.shortcuts import get_object_or_404, render,HttpResponse

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from django.shortcuts import redirect
from .models import Notification
from commentslikes.models import Comment, Reaction
# Create your views here.


def get_comments(user=None):
    if user:
        comments = Comment.objects.filter(Q(user=user) & Q(parent=None)).prefetch_related('replies').order_by('-created_at')
    else:
        comments = Comment.objects.filter(parent=None).prefetch_related('replies').order_by('-created_at')
    
    for comment in comments:
        comment.preview_replies = comment.replies.all().order_by('created_at')[:3]  # Primeros 3 replies
        comment.total_replies = comment.replies.count()
        comment.has_more_replies = comment.total_replies > 3


@login_required
def notifications_view(request):
    notifications = request.user.notifications.all().order_by('read')
    return render(request, 'notifications/partials/notifications_list.html', {'notifications': notifications})

@login_required
def mark_as_read(request, notification_id):
    notification = request.user.notifications.get(id=notification_id)
    notification.read = True
    notification.save()
    return redirect('notifications_view')

@login_required
def mark_all_read(request):
    request.user.notifications.filter(read=False).update(read=True)
    return redirect('notifications_view')

@login_required
def notification_detail(request, notification_id):
    # Obtener la notificación
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)

    # Verificar si el contenido de la notificación aún existe
    comment = notification.content_object
    if not comment or not Comment.objects.filter(id=getattr(comment, 'id', None)).exists():
        # Comentario eliminado: mostrar mensaje o redirigir
        notification.mark_as_read()
        return HttpResponse("El comentario asociado a esta notificación ya no existe.", status=404)

    # Determinar comentario raíz
    root_comment = comment.parent if comment.parent else comment

    comments_qs = Comment.objects.filter(id=root_comment.id)

    comments = []
    for c in comments_qs:
        replies_qs = c.replies.all().order_by('created_at') if hasattr(c, 'replies') else []
        total_replies = replies_qs.count() if hasattr(replies_qs, 'count') else 0
        comments.append({
            'comment': c,
            'preview_replies': replies_qs[:3],  # mostrar solo primeras 3
            'total_replies': total_replies,
            'has_more_replies': total_replies > 3,
        })

    # Marcar la notificación como leída
    notification.mark_as_read()

    context = {
        'parent': root_comment.parent if root_comment.parent else None,
        'comment': root_comment,
        'comments': comments,
    }
    return render(request, 'notifications/notification_detail.html', context)


@login_required
def notification_count(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user, 
            read=False
        ).count()
        return HttpResponse(str(unread_count))
    return HttpResponse('0')