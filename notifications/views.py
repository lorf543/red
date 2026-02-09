from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
# Create your views here.
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from django.shortcuts import redirect
from .models import Notification
from commentslikes.models import Comment, Reaction





@login_required
def notifications_view(request):
    """Retorna la lista de notificaciones del usuario"""
    notifications = request.user.notifications.all().order_by('-timestamp')[:20]  # Últimas 20
    return render(request, 'notifications/partials/notifications_list.html', {
        'notifications': notifications
    })

@login_required
def notification_redirect(request, notification_id):
    """Redirige al usuario al objeto de la notificación y marca como leída"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    
    # Redirigir a la URL del objeto
    redirect_url = notification.get_absolute_url()
    print("hola que hace")
    
    return redirect( 'notification_detail',notification_id=notification.id)

@login_required
def mark_notification_read(request, notification_id):
    """Marca una notificación como leída y retorna el item actualizado"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    
    # Actualizar el contador en el badge
    unread_count = request.user.notifications.filter(read=False).count()
    
    # Retornar el item actualizado
    response = render(request, 'notifications/partials/notification_item.html', {
        'notification': notification
    })
    
    # Agregar header para actualizar el contador
    response['HX-Trigger'] = f'{{"updateNotificationCount": {unread_count}}}'
    
    return response

@login_required
def mark_all_notifications_read(request):
    """Marca todas las notificaciones como leídas"""
    request.user.notifications.filter(read=False).update(read=True)
    
    # Retornar la lista actualizada
    notifications = request.user.notifications.all().order_by('-timestamp')[:20]
    response = render(request, 'notifications/partials/notifications_list.html', {
        'notifications': notifications
    })
    
    # Trigger para actualizar el contador a 0
    response['HX-Trigger'] = '{"updateNotificationCount": 0}'
    
    return response



@login_required
def notification_detail(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    obj = notification.content_object
    if not obj:
        return HttpResponse("Contenido no disponible", status=404)

    # Determinar comentario raíz
    if hasattr(obj, 'parent') and obj.parent:
        root_comment = obj.parent
        highlight_id = obj.id
    else:
        root_comment = obj
        highlight_id = obj.id

    notification.mark_as_read()

    context = {
        'comment': root_comment,
        'highlight_id': highlight_id,
    }

    return render(
        request,
        'notifications/notification_detail.html',
        context
    )


@login_required
def notification_count(request):
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user, 
            read=False
        ).count()
        return HttpResponse(str(unread_count))
    return HttpResponse('0')