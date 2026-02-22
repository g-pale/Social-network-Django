from celery import shared_task
from .models import Post
from PIL import Image
import os


@shared_task
def resize_post_image_task(post_id):
    """
    Фоновая задача для изменения размера изображения поста.
    Ограничивает максимальный размер (например, 800x800).
    """
    try:
        post = Post.objects.get(id=post_id)
        if not post.image:
            return

        image_path = post.image.path
        if not os.path.exists(image_path):
            return

        img = Image.open(image_path)
        # Если изображение больше 800x800, уменьшаем его
        if img.height > 800 or img.width > 800:
            output_size = (800, 800)
            img.thumbnail(output_size)
            img.save(image_path)

    except Post.DoesNotExist:
        pass
