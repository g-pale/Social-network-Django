from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Follow(models.Model):
    """
    Модель подписки пользователя на другого пользователя.
    follower - кто подписывается
    following - на кого подписываются
    """
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписка'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_follower_following'
            ),
        ]
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['following']),
        ]

    def __str__(self):
        return f'{self.follower.username} подписан на {self.following.username}'

    def clean(self):
        """Валидация: нельзя подписаться на самого себя"""
        if self.follower == self.following:
            raise ValidationError('Нельзя подписаться на самого себя')

    def save(self, *args, **kwargs):
        """Вызываем clean() перед сохранением"""
        self.full_clean()
        super().save(*args, **kwargs)
