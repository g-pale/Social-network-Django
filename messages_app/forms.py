from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    """Форма для отправки сообщения"""

    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите сообщение...',
                'maxlength': 2000,
            })
        }
        labels = {
            'text': 'Сообщение'
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if not text:
            raise forms.ValidationError('Сообщение не может быть пустым')
        if len(text) > 2000:
            raise forms.ValidationError('Сообщение не может быть длиннее 2000 символов')
        return text
