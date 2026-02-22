from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.template import loader
from django.contrib.auth import get_user_model
from PIL import Image
import os
import base64
import uuid
from django.core.files.base import ContentFile

User = get_user_model()


class CustomPasswordResetForm(PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        from accounts.tasks import send_password_reset_email_task

        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        html_email = None
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context)

        send_password_reset_email_task.delay(
            subject=subject,
            body=body,
            from_email=from_email,
            to_email=to_email,
            html_email=html_email
        )


class UserRegisterForm(UserCreationForm):
    """
    Форма регистрации пользователя.
    Расширяет стандартную UserCreationForm.
    """
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email'
        })
    )
    username = forms.CharField(
        label='Имя пользователя',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        }),
        help_text='Обязательное поле. Не более 150 символов. Только буквы, цифры и @/./+/-/_'
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        }),
        help_text='Пароль должен содержать минимум 8 символов'
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтвердите пароль'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем Bootstrap классы ко всем полям
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                continue
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_username(self):
        """Проверка уникальности username"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким именем уже существует.')
        return username


class UserLoginForm(AuthenticationForm):
    """
    Форма входа пользователя.
    Расширяет стандартную AuthenticationForm.
    """
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем Bootstrap классы
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                continue
            field.widget.attrs['class'] = 'form-control'

    error_messages = {
        'invalid_login': 'Неверное имя пользователя или пароль.',
        'inactive': 'Этот аккаунт неактивен.',
    }


class UserProfileEditForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя.
    """
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email'
        })
    )
    first_name = forms.CharField(
        label='Имя',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя'
        })
    )
    last_name = forms.CharField(
        label='Фамилия',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        })
    )
    bio = forms.CharField(
        label='О себе',
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Расскажите о себе',
            'rows': 4
        })
    )
    avatar = forms.ImageField(
        label='Аватар',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'id_avatar_input'
        })
    )
    cropped_avatar = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'id_cropped_avatar'})
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'bio', 'avatar', 'cropped_avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем Bootstrap классы ко всем полям
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                continue
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data.get('email')
        # Исключаем текущего пользователя из проверки
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_avatar(self):
        """Валидация аватара"""
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Проверка размера файла (максимум 2 МБ)
            max_size = 2 * 1024 * 1024  # 2 МБ
            if avatar.size > max_size:
                raise forms.ValidationError('Размер аватара не должен превышать 2 МБ.')

            # Проверка типа файла
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = os.path.splitext(avatar.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError('Разрешены только изображения: JPG, JPEG, PNG, GIF, WEBP.')

            # Проверка MIME типа
            if hasattr(avatar, 'content_type'):
                allowed_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
                if avatar.content_type not in allowed_mime_types:
                    raise forms.ValidationError('Недопустимый тип файла.')

            # Проверка реального содержимого через Pillow
            try:
                img = Image.open(avatar)
                img.verify()
                avatar.seek(0)  # Сбрасываем указатель после verify
            except Exception:
                raise forms.ValidationError('Файл повреждён или не является изображением.')

        return avatar

    def save(self, commit=True):
        user = super().save(commit=False)
        cropped_avatar_data = self.cleaned_data.get('cropped_avatar')

        if cropped_avatar_data:
            format, imgstr = cropped_avatar_data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f"avatar_{uuid.uuid4().hex}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=file_name)

            user.avatar = data

        if commit:
            user.save()
        return user
