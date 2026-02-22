from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.cache import cache
from .models import Post, Like, Comment
from .tasks import resize_post_image_task


@receiver([post_save, post_delete], sender=Post)
@receiver([post_save, post_delete], sender=Like)
@receiver([post_save, post_delete], sender=Comment)
def clear_post_cache(sender, **kwargs):
    """
    Очистка кэша ленты постов при изменении постов, лайков или комментариев.
    """
    cache.delete('all_posts_newest')
    cache.delete('all_posts_oldest')


@receiver(post_save, sender=Post)
def schedule_post_image_resize(sender, instance, created, **kwargs):
    """
    Триггерит задачу Celery для уменьшения картинки поста после сохранения.
    """
    if instance.image:
        transaction.on_commit(lambda: resize_post_image_task.delay(instance.id))
