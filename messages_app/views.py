from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Max, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Conversation, Message
from .forms import MessageForm
from notifications.utils import create_notification

User = get_user_model()


@login_required
def conversations_list(request):
    """
    View для отображения списка бесед пользователя.
    """
    # Получаем все беседы, в которых участвует текущий пользователь
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender_id=request.user.id))
    ).order_by('-last_message_time', '-updated_at')

    # Помечаем все уведомления о сообщениях как прочитанные при открытии списка бесед
    # (пользователь видит список, значит он уже знает о сообщениях)
    from notifications.models import Notification
    Notification.objects.filter(
        recipient=request.user,
        notification_type='message',
        is_read=False
    ).update(is_read=True)

    # Добавляем информацию о другом участнике и последнем сообщении
    conversations_with_info = []
    for conv in conversations:
        other_participant = conv.get_other_participant(request.user)
        last_message = conv.messages.order_by('-created_at').first()
        conversations_with_info.append({
            'conversation': conv,
            'other_participant': other_participant,
            'last_message': last_message,
            'unread_count': conv.unread_count,
        })

    context = {
        'conversations': conversations_with_info,
    }

    return render(request, 'messages_app/conversations_list.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """
    View для отображения конкретной беседы.
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    # Получаем другого участника
    other_participant = conversation.get_other_participant(request.user)

    # Проверяем, что другой участник существует
    if not other_participant:
        messages.error(request, 'Ошибка: беседа не найдена или некорректна.')
        return redirect('messages_app:conversations')

    # Удаляем ВСЕ уведомления о сообщениях при открытии любой беседы
    # (они не нужны, так как пользователь уже видит сообщения в беседе)
    # Это нужно делать ДО получения сообщений, чтобы уведомления не успели отобразиться
    from notifications.models import Notification
    Notification.objects.filter(
        recipient=request.user,
        notification_type='message'
    ).delete()

    # Получаем сообщения
    conversation_messages = conversation.messages.select_related('sender').order_by('created_at')

    # Пагинация
    paginator = Paginator(conversation_messages, 50)
    page = request.GET.get('page', 1)

    try:
        messages_page = paginator.page(page)
    except PageNotAnInteger:
        messages_page = paginator.page(1)
    except EmptyPage:
        messages_page = paginator.page(paginator.num_pages)

    # Отмечаем сообщения как прочитанные
    Message.objects.filter(
        conversation=conversation
    ).exclude(
        sender=request.user
    ).filter(
        is_read=False
    ).update(is_read=True)

    # Форма для отправки сообщения
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()

            # Обновляем время обновления беседы
            conversation.save()

            # Создаем уведомление для получателя
            create_notification(
                recipient=other_participant,
                actor=request.user,
                notification_type='message',
                conversation=conversation
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': {
                        'id': message.id,
                        'text': message.text,
                        'sender': message.sender.username,
                        'created_at': message.created_at.strftime('%d.%m.%Y %H:%M'),
                        'avatar_url': message.sender.avatar.url if message.sender.avatar else None,
                    }
                })

            return redirect('messages_app:conversation', conversation_id=conversation_id)
    else:
        form = MessageForm()

    context = {
        'conversation': conversation,
        'other_participant': other_participant,
        'messages': messages_page,
        'form': form,
        'is_paginated': paginator.num_pages > 1,
    }

    return render(request, 'messages_app/conversation.html', context)


@login_required
def start_conversation(request, username):
    """
    View для начала новой беседы с пользователем.
    """
    other_user = get_object_or_404(User, username=username)

    # Нельзя начать беседу с самим собой
    if request.user == other_user:
        return redirect('messages_app:conversations')

    # Ищем существующую беседу
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).distinct().first()

    # Если беседы нет, создаем новую
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)

    return redirect('messages_app:conversation', conversation_id=conversation.id)


@login_required
def send_message(request, conversation_id):
    """
    View для отправки сообщения через AJAX.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    form = MessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        message.save()

        # Обновляем время обновления беседы
        conversation.save()

        # Получаем другого участника
        other_participant = conversation.get_other_participant(request.user)

        # Создаем уведомление
        create_notification(
            recipient=other_participant,
            actor=request.user,
            notification_type='message',
            conversation=conversation
        )

        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'text': message.text,
                'sender': message.sender.username,
                'created_at': message.created_at.strftime('%d.%m.%Y %H:%M'),
                'avatar_url': message.sender.avatar.url if message.sender.avatar else None,
            }
        })
    else:
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = error_list[0] if error_list else ''
        return JsonResponse({'error': 'Ошибка валидации', 'errors': errors}, status=400)
