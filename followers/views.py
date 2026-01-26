from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db import transaction
from django.db.utils import OperationalError
import time
from .models import Follow
from notifications.utils import create_notification

User = get_user_model()


@login_required
def toggle_follow(request, username):
    """
    View для подписки/отписки на пользователя (поддерживает AJAX и обычные запросы).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)
    
    target_user = get_object_or_404(User, username=username)
    
    # Нельзя подписаться на самого себя
    if request.user == target_user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Нельзя подписаться на самого себя'}, status=400)
        messages.error(request, 'Нельзя подписаться на самого себя.')
        return redirect('accounts:profile', username=username)
    
    # Используем транзакцию с повторными попытками при блокировке БД
    max_retries = 3
    retry_delay = 0.1  # 100ms
    
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Проверяем существование подписки
                follow_exists = Follow.objects.filter(
                    follower=request.user,
                    following=target_user
                ).exists()
                
                if follow_exists:
                    # Если уже подписан, отписываемся
                    Follow.objects.filter(
                        follower=request.user,
                        following=target_user
                    ).delete()
                    action = 'unfollowed'
                else:
                    # Подписываемся (используем get_or_create для защиты от race condition)
                    follow, created = Follow.objects.get_or_create(
                        follower=request.user,
                        following=target_user
                    )
                    action = 'followed'
                    # Создаем уведомление для пользователя, на которого подписались
                    if created:
                        create_notification(
                            recipient=target_user,
                            actor=request.user,
                            notification_type='follow'
                        )
            
            # Если успешно, выходим из цикла
            break
            
        except OperationalError as e:
            # Если база данных заблокирована, повторяем попытку
            if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Увеличиваем задержку с каждой попыткой
                continue
            else:
                # Если все попытки исчерпаны, возвращаем ошибку
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'База данных временно недоступна. Попробуйте позже.'}, status=503)
                messages.error(request, 'Произошла ошибка. Попробуйте позже.')
                return redirect('accounts:profile', username=username)
        except Exception as e:
            # Обработка других ошибок
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Произошла ошибка при обработке запроса'}, status=500)
            messages.error(request, 'Произошла ошибка.')
            return redirect('accounts:profile', username=username)
    
    # Получаем актуальные данные
    followers_count = target_user.get_followers_count()
    is_following = Follow.objects.filter(
        follower=request.user,
        following=target_user
    ).exists()
    
    # Если это AJAX запрос, возвращаем JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'action': action,
            'followers_count': followers_count,
            'is_following': is_following
        })
    
    # Обычный запрос - редирект с сообщением
    if action == 'followed':
        messages.success(request, f'Вы подписались на {target_user.username}')
    else:
        messages.info(request, f'Вы отписались от {target_user.username}')
    
    return redirect('accounts:profile', username=username)


@login_required
def followers_list(request, username):
    """
    View для отображения списка подписчиков пользователя.
    """
    user = get_object_or_404(User, username=username)
    # Оптимизация: используем select_related для связанных объектов
    followers = User.objects.filter(
        following__following=user
    ).distinct()
    
    # Получаем информацию о подписках текущего пользователя одним запросом
    following_users = set()
    if request.user.is_authenticated:
        following_users = set(Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True))
    
    context = {
        'profile_user': user,
        'users': followers,
        'following_users': following_users,
        'list_type': 'followers',
        'title': f'Подписчики {user.username}'
    }
    
    return render(request, 'followers/users_list.html', context)


@login_required
def following_list(request, username):
    """
    View для отображения списка подписок пользователя.
    """
    user = get_object_or_404(User, username=username)
    # Оптимизация: используем distinct для избежания дубликатов
    following = User.objects.filter(
        followers__follower=user
    ).distinct()
    
    # Получаем информацию о подписках текущего пользователя одним запросом
    following_users = set()
    if request.user.is_authenticated:
        following_users = set(Follow.objects.filter(
            follower=request.user
        ).values_list('following_id', flat=True))
    
    context = {
        'profile_user': user,
        'users': following,
        'following_users': following_users,
        'list_type': 'following',
        'title': f'Подписки {user.username}'
    }
    
    return render(request, 'followers/users_list.html', context)
