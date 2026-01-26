from .models import Notification


def unread_notifications_count(request):
    """
    Context processor для добавления количества непрочитанных уведомлений
    во все шаблоны.
    Уведомления о сообщениях исключены, так как они отображаются отдельно в разделе "Сообщения".
    """
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).exclude(
            notification_type='message'  # Исключаем уведомления о сообщениях
        ).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}
