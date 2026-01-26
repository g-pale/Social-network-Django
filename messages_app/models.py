from django.db import models
from django.conf import settings
from django.urls import reverse


class Conversation(models.Model):
    """
    Модель беседы между двумя пользователями.
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name='Участники'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Беседа'
        verbose_name_plural = 'Беседы'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        participants_list = ', '.join([p.username for p in self.participants.all()[:2]])
        return f'Беседа: {participants_list}'

    def get_other_participant(self, user):
        """Возвращает другого участника беседы"""
        return self.participants.exclude(id=user.id).first()

    def get_unread_count(self, user):
        """Возвращает количество непрочитанных сообщений для пользователя"""
        return self.messages.filter(
            sender__ne=user,
            is_read=False
        ).count()


class Message(models.Model):
    """
    Модель сообщения в беседе.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Беседа'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Отправитель'
    )
    text = models.TextField(
        max_length=2000,
        verbose_name='Текст сообщения'
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name='Прочитано'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'is_read']),
        ]

    def __str__(self):
        return f'Сообщение от {self.sender.username} ({self.created_at.strftime("%d.%m.%Y %H:%M")})'

    def get_absolute_url(self):
        return reverse('messages_app:conversation', kwargs={'conversation_id': self.conversation.id})
