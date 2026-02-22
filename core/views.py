from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth import get_user_model
from posts.models import Post
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

User = get_user_model()


def search(request):
    """
    View для поиска по постам и пользователям.
    """
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'all')  # 'all', 'posts', 'users'

    posts_results = None
    users_results = None

    if query:
        q_lower = query.lower()
        q_title = query.title()
        q_upper = query.upper()

        if search_type in ['all', 'posts']:
            # Поиск по постам (обход бага SQLite с регистром кириллицы)
            posts_queryset = Post.objects.filter(
                Q(text__icontains=query) | Q(text__icontains=q_lower) | Q(text__icontains=q_title) | Q(text__icontains=q_upper) |
                Q(author__username__icontains=query) | Q(author__username__icontains=q_lower) | Q(author__username__icontains=q_title) | Q(author__username__icontains=q_upper)
            ).select_related('author').prefetch_related('likes', 'comments').order_by('-created_at')

            # Пагинация для постов
            posts_paginator = Paginator(posts_queryset, 10)
            posts_page = request.GET.get('posts_page', 1)
            try:
                posts_results = posts_paginator.page(posts_page)
            except PageNotAnInteger:
                posts_results = posts_paginator.page(1)
            except EmptyPage:
                posts_results = posts_paginator.page(posts_paginator.num_pages)

        if search_type in ['all', 'users']:
            # Поиск по пользователям (обход бага SQLite с регистром кириллицы)
            users_queryset = User.objects.filter(
                Q(username__icontains=query) | Q(username__icontains=q_lower) | Q(username__icontains=q_title) | Q(username__icontains=q_upper) |
                Q(first_name__icontains=query) | Q(first_name__icontains=q_lower) | Q(first_name__icontains=q_title) | Q(first_name__icontains=q_upper) |
                Q(last_name__icontains=query) | Q(last_name__icontains=q_lower) | Q(last_name__icontains=q_title) | Q(last_name__icontains=q_upper)
            ).order_by('-date_joined')

            # Пагинация для пользователей
            users_paginator = Paginator(users_queryset, 12)
            users_page = request.GET.get('users_page', 1)
            try:
                users_results = users_paginator.page(users_page)
            except PageNotAnInteger:
                users_results = users_paginator.page(1)
            except EmptyPage:
                users_results = users_paginator.page(users_paginator.num_pages)

    context = {
        'query': query,
        'search_type': search_type,
        'posts_results': posts_results,
        'users_results': users_results,
    }

    return render(request, 'core/search.html', context)
