from django.db import models
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os


class Post(models.Model):
    """
    Модель поста пользователя.
    Содержит текст (до 1000 символов) и опциональное изображение.
    """
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    text = models.TextField(
        max_length=1000,
        verbose_name='Текст поста'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True,
        verbose_name='Изображение'
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
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return f'Пост от {self.author.username} ({self.created_at.strftime("%d.%m.%Y %H:%M")})'

    def get_absolute_url(self):
        return reverse('posts:detail', kwargs={'pk': self.pk})

    def get_likes_count(self):
        """Возвращает количество лайков на пост"""
        return self.likes.count()

    def get_comments_count(self):
        """Возвращает количество комментариев к посту"""
        return self.comments.count()

    def is_liked_by(self, user):
        """Проверяет, лайкнул ли пользователь этот пост"""
        if not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()
    
    def clean(self):
        """Валидация на уровне модели"""
        super().clean()
        
        # Проверка длины текста
        if self.text:
            text_stripped = self.text.strip()
            if not text_stripped:
                raise ValidationError({'text': 'Текст поста не может быть пустым.'})
            if len(text_stripped) > 1000:
                raise ValidationError({'text': 'Текст поста не может превышать 1000 символов.'})
    
    def save(self, *args, **kwargs):
        """Переопределяем save для вызова clean"""
        self.full_clean()
        super().save(*args, **kwargs)


class Like(models.Model):
    """
    Модель лайка на пост.
    Один пользователь может поставить только один лайк на пост.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Пользователь'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Пост'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
        unique_together = ['user', 'post']  # Один пользователь - один лайк на пост
        indexes = [
            models.Index(fields=['post', 'user']),
        ]

    def __str__(self):
        return f'{self.user.username} лайкнул пост #{self.post.id}'


class Comment(models.Model):
    """
    Модель комментария к посту.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        max_length=500,
        verbose_name='Текст комментария'
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
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self):
        return f'Комментарий от {self.author.username} к посту #{self.post.id}'
    
    def clean(self):
        """Валидация на уровне модели"""
        super().clean()
        
        # Проверка длины текста
        if self.text:
            text_stripped = self.text.strip()
            if not text_stripped:
                raise ValidationError({'text': 'Текст комментария не может быть пустым.'})
            if len(text_stripped) > 500:
                raise ValidationError({'text': 'Текст комментария не может превышать 500 символов.'})
    
    def save(self, *args, **kwargs):
        """Переопределяем save для вызова clean"""
        self.full_clean()
        super().save(*args, **kwargs)