from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
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
            # Редирект на страницу, с которой пришел пользователь, или на главную
            next_url = request.GET.get('next', 'posts:home')
            return redirect(next_url)
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
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
    
    # Получаем посты пользователя
    posts = Post.objects.filter(author=profile_user).select_related('author').order_by(order_by)[:10]
    
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
    users = User.objects.all().order_by('-date_joined')
    
    # Если пользователь авторизован, исключаем его из списка
    if request.user.is_authenticated:
        users = users.exclude(pk=request.user.pk)
    
    context = {
        'users': users,
    }
    
    return render(request, 'accounts/users_list.html', context)
