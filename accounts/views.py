from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import UserRegisterForm, UserLoginForm, UserProfileEditForm
from posts.models import Post
from followers.models import Follow

User = get_user_model()


def register_view(request):
    """
    View для регистрации нового пользователя.
    """
    if request.user.is_authenticated:
        messages.info(request, 'Вы уже авторизованы.')
        return redirect('posts:home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Аккаунт для {username} успешно создан! Теперь вы можете войти.')
            # Автоматически входим после регистрации
            login(request, user)
            return redirect('posts:home')
        else:
            # Сообщения об ошибках уже есть в форме
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    View для входа пользователя.
    """
    if request.user.is_authenticated:
        messages.info(request, 'Вы уже авторизованы.')
        return redirect('posts:home')

    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            # AuthenticationForm уже проверил пользователя
            user = form.get_user()
            login(request, user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Добро пожаловать, {username}!')
            # Редиректим только на безопасные локальные URL.
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('posts:home')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    """
    View для выхода пользователя из системы.
    """
    username = request.user.username
    logout(request)
    messages.success(request, f'Вы успешно вышли из системы. До свидания, {username}!')
    return redirect('posts:home')


def profile_view(request, username):
    """
    View для отображения профиля пользователя.
    """
    profile_user = get_object_or_404(User, username=username)

    # Получаем параметр сортировки из GET-запроса
    sort_type = request.GET.get('sort', 'newest')  # 'newest' или 'oldest'

    # Определяем порядок сортировки
    if sort_type == 'oldest':
        order_by = 'created_at'  # Старые сверху
    else:
        order_by = '-created_at'  # Новые сверху (по умолчанию)

    # Получаем посты пользователя с пагинацией
    posts_queryset = Post.objects.filter(author=profile_user).select_related('author').order_by(order_by)

    paginator = Paginator(posts_queryset, 10)
    page = request.GET.get('page', 1)

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    # Статистика
    posts_count = profile_user.get_posts_count()
    followers_count = profile_user.get_followers_count()
    following_count = profile_user.get_following_count()

    # Проверяем, подписан ли текущий пользователь на этого пользователя
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=profile_user
        ).exists()

    # Проверяем, является ли это профиль текущего пользователя
    is_own_profile = request.user.is_authenticated and request.user == profile_user

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'posts_count': posts_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
        'is_own_profile': is_own_profile,
        'sort_type': sort_type,
        'is_paginated': paginator.num_pages > 1,
    }

    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    """
    View для редактирования профиля пользователя.
    """
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('accounts:profile', username=request.user.username)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = UserProfileEditForm(instance=request.user)

    return render(request, 'accounts/profile_edit.html', {'form': form})


def users_list_view(request):
    """
    View для отображения списка всех пользователей.
    """
    users_queryset = User.objects.all().order_by('-date_joined')

    # Если пользователь авторизован, исключаем его из списка
    if request.user.is_authenticated:
        users_queryset = users_queryset.exclude(pk=request.user.pk)

    # Пагинация: 12 пользователей на страницу
    paginator = Paginator(users_queryset, 12)
    page = request.GET.get('page', 1)

    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    context = {
        'users': users,
        'is_paginated': paginator.num_pages > 1,
    }

    return render(request, 'accounts/users_list.html', context)

