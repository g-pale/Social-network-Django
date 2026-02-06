from .models import Notification


def create_notification(recipient, actor, notification_type, post=None, comment=None, conversation=None):
    """
    Утилита для создания уведомления.

    Args:
        recipient: Пользователь, который получит уведомление
        actor: Пользователь, который выполнил действие
        notification_type: Тип уведомления ('like', 'comment', 'follow', 'message')
        post: Пост (опционально, для like и comment)
        comment: Комментарий (опционально, для comment)
        conversation: Беседа (опционально, для message)

    Returns:
        Notification объект или None
    """
    # Не создаем уведомление, если пользователь выполняет действие над своим контентом
    if recipient == actor:
        return None

    # Проверяем, не существует ли уже такое уведомление (защита от дублирования)
    # Для лайков и комментариев проверяем по посту и типу
    if notification_type in ['like', 'comment'] and post:
        # Проверяем, не было ли уже создано уведомление для этого поста от этого пользователя
        # в последние 5 секунд (защита от двойных кликов и race conditions)
        from django.utils import timezone
        from datetime import timedelta

        recent_notification = Notification.objects.filter(
            recipient=recipient,
            actor=actor,
            notification_type=notification_type,
            post=post,
            created_at__gte=timezone.now() - timedelta(seconds=5)
        ).first()

        if recent_notification:
            # Уведомление уже было создано недавно, не создаем дубликат
            return recent_notification

    # Создаем уведомление
    notification = Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=notification_type,
        post=post,
        comment=comment,
        conversation=conversation
    )

    return notification
