from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model
from .tasks import resize_avatar_task

User = get_user_model()


@receiver(post_save, sender=User)
def schedule_avatar_resize(sender, instance, created, **kwargs):
    """
    Триггерит задачу Celery для уменьшения аватара после сохранения профиля.
    """
    if instance.avatar:
        transaction.on_commit(lambda: resize_avatar_task.delay(instance.id))
