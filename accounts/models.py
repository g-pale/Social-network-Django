from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """
    Кастомная модель пользователя, расширяющая AbstractUser.
    Добавляет возможность загрузки аватара и другие поля при необходимости.
    """
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='О себе'
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата регистрации'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'username': self.username})

    def get_posts_count(self):
        """Возвращает количество постов пользователя"""
        return self.posts.count()

    def get_followers_count(self):
        """Возвращает количество подписчиков"""
        return self.followers.count()

    def get_following_count(self):
        """Возвращает количество подписок"""
        return self.following.count()
