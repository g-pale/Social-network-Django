from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from PIL import Image
import os

User = get_user_model()


@shared_task
def send_password_reset_email_task(subject, body, from_email, to_email, html_email=None):
    """
    Фоновая задача для отправки email сброса пароля.
    """
    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email is not None:
        email_message.attach_alternative(html_email, "text/html")
    email_message.send()


@shared_task
def resize_avatar_task(user_id):
    """
    Фоновая задача для изменения размера аватара.
    Ограничивает максимальный размер (например, 300x300).
    """
    try:
        user = User.objects.get(id=user_id)
        if not user.avatar:
            return

        avatar_path = user.avatar.path
        if not os.path.exists(avatar_path):
            return

        img = Image.open(avatar_path)
        # Если аватар больше 300x300, уменьшаем его
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(avatar_path)

    except User.DoesNotExist:
        pass
