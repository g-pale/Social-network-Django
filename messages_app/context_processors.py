from .models import Conversation, Message


def unread_messages_count(request):
    """
    Context processor для добавления количества непрочитанных сообщений
    во все шаблоны.
    """
    if request.user.is_authenticated:
        # Получаем все беседы пользователя
        conversations = Conversation.objects.filter(participants=request.user)
        
        # Подсчитываем непрочитанные сообщения
        unread_count = Message.objects.filter(
            conversation__in=conversations
        ).exclude(
            sender=request.user
        ).filter(
            is_read=False
        ).count()
        
        return {'unread_messages_count': unread_count}
    return {'unread_messages_count': 0}
