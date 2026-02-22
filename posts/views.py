from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from .models import Post, Like, Comment
from .forms import PostForm, CommentForm
from followers.models import Follow
from notifications.utils import create_notification
from notifications.models import Notification


def home(request):
    """Главная страница с лентой постов"""
    # Получаем параметры фильтра и сортировки из GET-запроса
    filter_type = request.GET.get('filter', 'all')  # 'all' или 'following'
    sort_type = request.GET.get('sort', 'newest')  # 'newest' или 'oldest'

    # Определяем порядок сортировки
    if sort_type == 'oldest':
        order_by = 'created_at'  # Старые сверху
    else:
        order_by = '-created_at'  # Новые сверху (по умолчанию)

    # Получаем посты в зависимости от фильтра
    if request.user.is_authenticated and filter_type == 'following':
        # Получаем список ID пользователей, на которых подписан текущий пользователь
        following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        # Добавляем текущего пользователя, чтобы видеть свои посты
        following_ids = list(following_ids) + [request.user.id]
        posts = (
            Post.objects.filter(author_id__in=following_ids)
            .select_related('author')
            .annotate(
                annotated_likes_count=Count('likes', distinct=True),
                annotated_comments_count=Count('comments', distinct=True),
            )
            .order_by(order_by)
        )
    else:
        # Показываем все посты
        posts = (
            Post.objects.all()
            .select_related('author')
            .annotate(
                annotated_likes_count=Count('likes', distinct=True),
                annotated_comments_count=Count('comments', distinct=True),
            )
            .order_by(order_by)
        )

    # Пагинация: 10 постов на страницу
    paginator = Paginator(posts, 10)
    page = request.GET.get('page', 1)

    try:
        posts_page = paginator.page(page)
    except PageNotAnInteger:
        posts_page = paginator.page(1)
    except EmptyPage:
        posts_page = paginator.page(paginator.num_pages)

    # Batch-проверка лайков: один запрос вместо N
    liked_post_ids = set()
    if request.user.is_authenticated:
        page_post_ids = [post.pk for post in posts_page]
        liked_post_ids = set(
            Like.objects.filter(user=request.user, post_id__in=page_post_ids)
            .values_list('post_id', flat=True)
        )

    # Добавляем информацию о лайках для каждого поста
    posts_with_likes = []
    for post in posts_page:
        posts_with_likes.append({
            'post': post,
            'is_liked': post.pk in liked_post_ids,
        })

    context = {
        'posts_with_likes': posts_with_likes,
        'posts': posts_page,  # Оставляем для обратной совместимости
        'filter_type': filter_type,
        'sort_type': sort_type,
        'is_paginated': paginator.num_pages > 1,
    }
    return render(request, 'posts/home.html', context)


@login_required
def create(request):
    """View для создания нового поста"""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Пост успешно создан!')
            return redirect('posts:detail', pk=post.pk)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PostForm()

    return render(request, 'posts/create.html', {'form': form})


def detail(request, pk):
    """View для отображения детальной страницы поста"""
    post = get_object_or_404(Post.objects.select_related('author').prefetch_related('likes', 'comments'), pk=pk)

    # Проверяем, лайкнул ли текущий пользователь этот пост
    is_liked = False
    if request.user.is_authenticated:
        is_liked = post.is_liked_by(request.user)

    # Получаем комментарии к посту
    comments = post.comments.select_related('author').order_by('created_at')

    # Форма для комментария (только для авторизованных)
    # Обработка POST запросов для комментариев происходит через create_comment view (AJAX)
    comment_form = None
    if request.user.is_authenticated:
        comment_form = CommentForm()

    context = {
        'post': post,
        'is_liked': is_liked,
        'comments': comments,
        'comment_form': comment_form,
    }

    return render(request, 'posts/detail.html', context)


@login_required
def edit(request, pk):
    """View для редактирования поста (только автор)"""
    post = get_object_or_404(Post, pk=pk)

    # Проверяем, что текущий пользователь является автором поста
    if post.author != request.user:
        messages.error(request, 'У вас нет прав для редактирования этого поста.')
        return redirect('posts:detail', pk=pk)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пост успешно обновлен!')
            return redirect('posts:detail', pk=post.pk)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PostForm(instance=post)

    return render(request, 'posts/edit.html', {'form': form, 'post': post})


@login_required
def delete(request, pk):
    """View для удаления поста (только автор)"""
    post = get_object_or_404(Post, pk=pk)

    # Проверяем, что текущий пользователь является автором поста
    if post.author != request.user:
        messages.error(request, 'У вас нет прав для удаления этого поста.')
        return redirect('posts:detail', pk=pk)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Пост успешно удален!')
        return redirect('posts:home')

    return render(request, 'posts/delete.html', {'post': post})


@login_required
def toggle_like(request, pk):
    """View для добавления/удаления лайка на пост (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    post = get_object_or_404(Post, pk=pk)

    # Проверяем, что пользователь не пытается лайкнуть свой собственный пост
    if post.author == request.user:
        return JsonResponse({'error': 'Нельзя ставить лайк на свой собственный пост'}, status=400)

    # Проверяем, существует ли уже лайк
    like_exists = Like.objects.filter(user=request.user, post=post).exists()

    if like_exists:
        # Лайк уже существует, удаляем его
        Like.objects.filter(user=request.user, post=post).delete()
        action = 'unliked'

        # Удаляем уведомление о лайке, если оно было создано
        # (если лайк был поставлен по ошибке и сразу снят, уведомления не должно быть)
        Notification.objects.filter(
            recipient=post.author,
            actor=request.user,
            notification_type='like',
            post=post
        ).delete()
    else:
        # Лайка нет, создаем его
        # Используем get_or_create с обработкой IntegrityError для защиты от race condition
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if created:
            # Лайк был создан, создаем уведомление
            action = 'liked'
            create_notification(
                recipient=post.author,
                actor=request.user,
                notification_type='like',
                post=post
            )
        else:
            # Лайк уже существовал (race condition), просто отмечаем как liked
            action = 'liked'

    # Получаем актуальное количество лайков напрямую из БД
    likes_count = Like.objects.filter(post=post).count()
    is_liked = Like.objects.filter(user=request.user, post=post).exists()

    # Возвращаем JSON ответ
    return JsonResponse({
        'action': action,
        'likes_count': likes_count,
        'is_liked': is_liked
    })


@login_required
def create_comment(request, pk):
    """View для создания комментария к посту (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)

    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()

        # Создаем уведомление для автора поста
        create_notification(
            recipient=post.author,
            actor=request.user,
            notification_type='comment',
            post=post,
            comment=comment
        )

        # Возвращаем данные нового комментария
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'text': comment.text,
                'author': comment.author.username,
                'author_url': (
                    comment.author.get_absolute_url()
                    if hasattr(comment.author, 'get_absolute_url')
                    else f'/accounts/profile/{comment.author.username}/'
                ),
                'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
                'avatar_url': comment.author.avatar.url if comment.author.avatar else None,
            },
            'comments_count': post.get_comments_count()
        })
    else:
        # Возвращаем ошибки валидации
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = error_list[0] if error_list else ''
        return JsonResponse({'error': 'Ошибка валидации', 'errors': errors}, status=400)


@login_required
def delete_comment(request, pk):
    """View для удаления комментария (только автор)"""
    comment = get_object_or_404(Comment, pk=pk)

    # Проверяем, что текущий пользователь является автором комментария
    if comment.author != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'У вас нет прав для удаления этого комментария'}, status=403)
        messages.error(request, 'У вас нет прав для удаления этого комментария.')
        return redirect('posts:detail', pk=comment.post.pk)

    post_pk = comment.post.pk

    if request.method == 'POST':
        comment.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX запрос
            post = get_object_or_404(Post, pk=post_pk)
            return JsonResponse({
                'success': True,
                'comments_count': post.get_comments_count()
            })
        else:
            # Обычный запрос
            messages.success(request, 'Комментарий успешно удален!')
            return redirect('posts:detail', pk=post_pk)

    # GET запрос - показываем страницу подтверждения
    return render(request, 'posts/delete_comment.html', {'comment': comment})
