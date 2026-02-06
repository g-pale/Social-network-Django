from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Notification


@login_required
def notifications_list(request):
    """
    View для отображения списка уведомлений пользователя.
    Уведомления о сообщениях исключены, так как они отображаются в окне беседы.
    """
    notifications = Notification.objects.filter(
        recipient=request.user
    ).exclude(
        notification_type='message'  # Исключаем уведомления о сообщениях
    ).select_related('actor', 'post', 'comment', 'conversation').order_by('-created_at')

    # Пагинация
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page', 1)

    try:
        notifications_page = paginator.page(page)
    except PageNotAnInteger:
        notifications_page = paginator.page(1)
    except EmptyPage:
        notifications_page = paginator.page(paginator.num_pages)

    context = {
        'notifications': notifications_page,
        'is_paginated': paginator.num_pages > 1,
    }

    return render(request, 'notifications/list.html', context)


@login_required
def mark_as_read(request, notification_id):
    """
    View для отметки уведомления как прочитанного (AJAX).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.is_read = True
        notification.save()

        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Уведомление не найдено'}, status=404)


@login_required
def mark_all_as_read(request):
    """
    View для отметки всех уведомлений как прочитанных.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('notifications:list')


@login_required
def unread_count(request):
    """
    View для получения количества непрочитанных уведомлений (AJAX).
    Уведомления о сообщениях исключены, так как они отображаются отдельно в разделе "Сообщения".
    """
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).exclude(
        notification_type='message'  # Исключаем уведомления о сообщениях
    ).count()

    return JsonResponse({'count': count})
