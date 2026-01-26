from django.db import models
from django.conf import settings
from django.urls import reverse


class Notification(models.Model):
    """
    Модель уведомления для пользователя.
    """
    NOTIFICATION_TYPES = [
        ('like', 'Лайк'),
        ('comment', 'Комментарий'),
        ('follow', 'Подписка'),
        ('message', 'Сообщение'),
    ]
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Получатель'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name='Отправитель'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name='Тип уведомления'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    # Опциональные связи для контекста
    post = models.ForeignKey(
        'posts.Post',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Пост'
    )
    comment = models.ForeignKey(
        'posts.Comment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Комментарий'
    )
    conversation = models.ForeignKey(
        'messages_app.Conversation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Беседа'
    )
    
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        type_names = {
            'like': 'лайкнул',
            'comment': 'прокомментировал',
            'follow': 'подписался на вас',
            'message': 'отправил сообщение'
        }
        return f'{self.actor.username} {type_names.get(self.notification_type, "")}'
    
    def get_message(self):
        """Возвращает текстовое сообщение уведомления"""
        messages = {
            'like': f'{self.actor.username} лайкнул ваш пост',
            'comment': f'{self.actor.username} прокомментировал ваш пост',
            'follow': f'{self.actor.username} подписался на вас',
            'message': f'{self.actor.username} отправил вам сообщение',
        }
        return messages.get(self.notification_type, 'Новое уведомление')
    
    def get_url(self):
        """Возвращает URL для перехода при клике на уведомление"""
        if self.notification_type == 'follow':
            return reverse('accounts:profile', kwargs={'username': self.actor.username})
        elif self.notification_type == 'message' and self.conversation:
            return reverse('messages_app:conversation', kwargs={'conversation_id': self.conversation.id})
        elif self.post:
            return reverse('posts:detail', kwargs={'pk': self.post.pk})
        return reverse('posts:home')
