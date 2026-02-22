from django import forms
from PIL import Image
from .models import Post, Comment
import os
import base64
import uuid
from django.core.files.base import ContentFile


class PostForm(forms.ModelForm):
    """
    Форма для создания и редактирования поста.
    """
    text = forms.CharField(
        label='Текст поста',
        max_length=1000,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Что у вас на уме? (максимум 1000 символов)',
            'rows': 6
        }),
        help_text='Максимум 1000 символов'
    )
    image = forms.ImageField(
        label='Изображение',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'id_image_input'
        }),
        help_text='Опционально. Вы можете прикрепить изображение к посту.'
    )
    cropped_image = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_cropped_image'})
    )

    class Meta:
        model = Post
        fields = ['text', 'image', 'cropped_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем Bootstrap классы ко всем полям
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                continue
            field.widget.attrs['class'] = 'form-control'

    def clean_text(self):
        """Валидация текста поста"""
        text = self.cleaned_data.get('text')
        if not text or not text.strip():
            raise forms.ValidationError('Текст поста не может быть пустым.')
        return text.strip()

    def clean_image(self):
        """Валидация изображения"""
        image = self.cleaned_data.get('image')
        if image:
            # Проверка размера файла (максимум 5 МБ)
            max_size = 5 * 1024 * 1024  # 5 МБ
            if image.size > max_size:
                raise forms.ValidationError('Размер изображения не должен превышать 5 МБ.')

            # Проверка типа файла
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError('Разрешены только изображения: JPG, JPEG, PNG, GIF, WEBP.')

            # Проверка MIME типа
            if hasattr(image, 'content_type'):
                allowed_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if image.content_type not in allowed_mime_types:
                    raise forms.ValidationError('Недопустимый тип файла.')

            # Проверка реального содержимого через Pillow
            try:
                img = Image.open(image)
                img.verify()
                image.seek(0)  # Сбрасываем указатель после verify
            except Exception:
                raise forms.ValidationError('Файл повреждён или не является изображением.')

        return image

    def save(self, commit=True):
        post = super().save(commit=False)
        cropped_image_data = self.cleaned_data.get('cropped_image')

        if cropped_image_data:
            # Убираем префикс `data:image/png;base64,`
            format, imgstr = cropped_image_data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f"{uuid.uuid4().hex}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=file_name)

            # Заменяем оригинальный файл обрезанным
            post.image = data

        if commit:
            post.save()
        return post


class CommentForm(forms.ModelForm):
    """
    Форма для создания комментария к посту.
    """
    text = forms.CharField(
        label='',
        max_length=500,
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Напишите комментарий... (максимум 500 символов)',
            'rows': 3
        }),
    )

    class Meta:
        model = Comment
        fields = ['text']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем Bootstrap классы ко всем полям
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                continue
            field.widget.attrs['class'] = 'form-control'

    def clean_text(self):
        """Валидация текста комментария"""
        text = self.cleaned_data.get('text')
        if not text or not text.strip():
            raise forms.ValidationError('Текст комментария не может быть пустым.')
        return text.strip()
