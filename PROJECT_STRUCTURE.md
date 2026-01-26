# Структура проекта MiniSocial

## Обзор

MiniSocial - это простая социальная сеть на Django, состоящая из нескольких приложений, каждое из которых отвечает за определенную функциональность.

## Архитектура приложений

### 1. accounts - Управление пользователями

**Назначение:** Аутентификация, регистрация и управление профилями пользователей.

**Модели:**
- `User` - кастомная модель пользователя (расширяет AbstractUser)
  - Поля: username, email, avatar, bio, date_joined
  - Методы: get_posts_count(), get_followers_count(), get_following_count()

**Views:**
- `register_view` - регистрация новых пользователей
- `login_view` - вход в систему
- `logout_view` - выход из системы
- `profile_view` - отображение профиля пользователя
- `profile_edit_view` - редактирование профиля
- `users_list_view` - список всех пользователей

**Forms:**
- `UserRegisterForm` - форма регистрации
- `UserLoginForm` - форма входа
- `UserProfileEditForm` - форма редактирования профиля

**URL-маршруты:**
- `/accounts/login/` - вход
- `/accounts/register/` - регистрация
- `/accounts/logout/` - выход
- `/accounts/profile/<username>/` - профиль пользователя
- `/accounts/profile/edit/` - редактирование профиля
- `/accounts/users/` - список пользователей
- `/accounts/password-reset/` - запрос сброса пароля
- `/accounts/password-reset/done/` - подтверждение отправки инструкций
- `/accounts/password-reset-confirm/<uidb64>/<token>/` - установка нового пароля
- `/accounts/password-reset-complete/` - успешное завершение сброса

---

### 2. posts - Посты, лайки и комментарии

**Назначение:** Управление постами, лайками и комментариями.

**Модели:**
- `Post` - модель поста
  - Поля: author, text (max 1000), image, created_at, updated_at
  - Методы: get_likes_count(), get_comments_count(), is_liked_by(user)
  
- `Like` - модель лайка
  - Поля: user, post, created_at
  - Ограничение: unique_together (user, post)
  
- `Comment` - модель комментария
  - Поля: post, author, text (max 500), created_at, updated_at

**Views:**
- `home` - главная страница с лентой постов (с пагинацией и фильтрами)
- `create` - создание нового поста
- `detail` - детальная страница поста с комментариями
- `edit` - редактирование поста (только автор)
- `delete` - удаление поста (только автор)
- `toggle_like` - AJAX добавление/удаление лайка
- `create_comment` - AJAX создание комментария
- `delete_comment` - удаление комментария (только автор)

**Forms:**
- `PostForm` - форма для создания/редактирования поста
- `CommentForm` - форма для создания комментария

**URL-маршруты:**
- `/` - главная страница (лента постов)
- `/create/` - создание поста
- `/<pk>/` - детальная страница поста
- `/<pk>/edit/` - редактирование поста
- `/<pk>/delete/` - удаление поста
- `/<pk>/like/` - AJAX лайк/анлайк
- `/<pk>/comment/` - AJAX создание комментария
- `/comment/<pk>/delete/` - удаление комментария

---

### 3. followers - Система подписок

**Назначение:** Управление подписками между пользователями.

**Модели:**
- `Follow` - модель подписки
  - Поля: follower (кто подписывается), following (на кого подписываются), created_at
  - Ограничение: unique_together (follower, following)
  - Защита от самоподписки в методе save()

**Views:**
- `toggle_follow` - AJAX подписка/отписка на пользователя
- `followers_list` - список подписчиков пользователя
- `following_list` - список подписок пользователя

**URL-маршруты:**
- `/follow/toggle/<username>/` - подписка/отписка
- `/follow/followers/<username>/` - список подписчиков
- `/follow/following/<username>/` - список подписок

---

### 4. core - Поиск и общие утилиты

**Назначение:** Поиск по постам и пользователям, общие утилиты.

**Views:**
- `search` - поиск по постам и пользователям с пагинацией

**URL-маршруты:**
- `/search/` - страница поиска

**Шаблоны:**
- `core/templates/core/search.html` - результаты поиска

---

### 5. notifications - Система уведомлений

**Назначение:** Уведомления о действиях других пользователей.

**Модели:**
- `Notification` - модель уведомления
  - Поля: recipient, actor, notification_type, is_read, created_at, post, comment, conversation
  - Типы: 'like', 'comment', 'follow', 'message'
  - Методы: get_message(), get_url()

**Views:**
- `notifications_list` - список уведомлений пользователя
- `mark_as_read` - отметка уведомления как прочитанного (AJAX)
- `mark_all_as_read` - отметка всех уведомлений как прочитанных
- `unread_count` - получение количества непрочитанных (AJAX)

**Utils:**
- `create_notification()` - утилита для создания уведомлений

**Context Processors:**
- `unread_notifications_count` - количество непрочитанных уведомлений во всех шаблонах

**URL-маршруты:**
- `/notifications/` - список уведомлений
- `/notifications/<id>/read/` - отметка как прочитанного
- `/notifications/mark-all-read/` - отметить все как прочитанные
- `/notifications/unread-count/` - количество непрочитанных

**Шаблоны:**
- `notifications/templates/notifications/list.html` - список уведомлений

---

### 6. messages_app - Личные сообщения

**Назначение:** Система личных сообщений между пользователями.

**Модели:**
- `Conversation` - модель беседы между двумя пользователями
  - Поля: participants (ManyToMany), created_at, updated_at
  - Методы: get_other_participant(user), get_unread_count(user)
  
- `Message` - модель сообщения
  - Поля: conversation, sender, text (max 2000), is_read, created_at

**Views:**
- `conversations_list` - список бесед пользователя
- `conversation_detail` - просмотр беседы с сообщениями
- `start_conversation` - начало новой беседы
- `send_message` - отправка сообщения через AJAX

**Forms:**
- `MessageForm` - форма для отправки сообщения

**Context Processors:**
- `unread_messages_count` - количество непрочитанных сообщений во всех шаблонах

**URL-маршруты:**
- `/messages/` - список бесед
- `/messages/start/<username>/` - начало беседы с пользователем
- `/messages/<conversation_id>/` - просмотр беседы
- `/messages/<conversation_id>/send/` - отправка сообщения (AJAX)

**Шаблоны:**
- `messages_app/templates/messages_app/conversations_list.html` - список бесед
- `messages_app/templates/messages_app/conversation.html` - беседа

---

### 7. config - Настройки проекта

**Назначение:** Основные настройки Django проекта.

**Файлы:**
- `settings.py` - настройки приложения
  - Безопасность: SECRET_KEY, DEBUG, ALLOWED_HOSTS через python-decouple
  - Установленные приложения: accounts, posts, followers, core, notifications, messages_app
  - Настройки статики и медиа
  - Настройки безопасности для production
  - Настройки email для сброса пароля
  - Context processors для уведомлений и сообщений
  
- `urls.py` - главный файл URL-маршрутов
  - Подключение URL-паттернов всех приложений
  - Обслуживание статики и медиа в режиме разработки

---

## Статические файлы

### JavaScript файлы

**static/js/likes.js**
- Обработка AJAX запросов для лайков
- Обновление UI без перезагрузки страницы
- Защита от двойных кликов

**static/js/comments.js**
- Обработка AJAX запросов для комментариев
- Создание и удаление комментариев
- Динамическое обновление списка комментариев

**static/js/follow.js**
- Обработка AJAX запросов для подписок
- Обновление кнопок подписки/отписки
- Обновление счетчиков подписчиков

**static/js/notifications.js**
- Обработка отметки уведомлений как прочитанных
- Автоматическое обновление счетчика уведомлений
- Обновление UI при клике на уведомление

**static/js/messages.js**
- AJAX отправка сообщений
- Автоматическая прокрутка к новым сообщениям
- Защита от двойной отправки

---

## Шаблоны

### Базовый шаблон

**templates/base.html**
- Навигационное меню
- Отображение сообщений (messages)
- Подключение Bootstrap 5 и Bootstrap Icons
- Блоки для расширения: content, extra_css, extra_js

### Шаблоны приложений

**accounts/templates/accounts/**
- `login.html` - форма входа
- `register.html` - форма регистрации
- `profile.html` - профиль пользователя
- `profile_edit.html` - редактирование профиля
- `users_list.html` - список всех пользователей
- `password_reset.html` - запрос сброса пароля
- `password_reset_done.html` - подтверждение отправки инструкций
- `password_reset_confirm.html` - установка нового пароля
- `password_reset_complete.html` - успешное завершение сброса
- `password_reset_email.html` - шаблон письма для сброса пароля
- `password_reset_subject.txt` - тема письма для сброса пароля

**posts/templates/posts/**
- `home.html` - лента постов с пагинацией
- `create.html` - создание поста
- `detail.html` - детальная страница поста
- `edit.html` - редактирование поста
- `delete.html` - подтверждение удаления поста
- `delete_comment.html` - подтверждение удаления комментария

**followers/templates/followers/**
- `users_list.html` - список подписчиков/подписок

**core/templates/core/**
- `search.html` - результаты поиска по постам и пользователям

**notifications/templates/notifications/**
- `list.html` - список уведомлений

**messages_app/templates/messages_app/**
- `conversations_list.html` - список бесед
- `conversation.html` - просмотр беседы с сообщениями

---

## База данных

### Модели и связи

```
User (accounts.User)
├── Post (posts.Post) [author]
│   ├── Like (posts.Like) [post]
│   └── Comment (posts.Comment) [post]
│
├── Follow (followers.Follow) [follower] - подписки пользователя
├── Follow (followers.Follow) [following] - подписчики пользователя
│
├── Conversation (messages_app.Conversation) [participants] - беседы пользователя
│   └── Message (messages_app.Message) [conversation] - сообщения в беседе
│
└── Notification (notifications.Notification) [recipient] - уведомления пользователя
    ├── Post (posts.Post) [post] - уведомление о посте
    ├── Comment (posts.Comment) [comment] - уведомление о комментарии
    └── Conversation (messages_app.Conversation) [conversation] - уведомление о сообщении
```

### Индексы

- Post: индекс на created_at, author
- Like: индекс на (post, user), unique_together (user, post)
- Comment: индекс на (post, created_at)
- Follow: unique_together (follower, following)

---

## Безопасность

### Реализованные меры

1. **Валидация данных:**
   - На уровне моделей (методы clean())
   - На уровне форм (методы clean_*())
   - Проверка типов и размеров файлов

2. **Права доступа:**
   - @login_required для защищенных views
   - Проверка авторства для редактирования/удаления

3. **CSRF защита:**
   - Включена для всех форм
   - Обработка CSRF токенов в AJAX запросах

4. **Безопасность файлов:**
   - Проверка типов файлов (расширения и MIME-типы)
   - Ограничение размеров (посты: 5 МБ, аватары: 2 МБ)
   - Разрешенные форматы: JPG, JPEG, PNG, GIF, WEBP

5. **Заголовки безопасности (production):**
   - SECURE_SSL_REDIRECT
   - SESSION_COOKIE_SECURE
   - CSRF_COOKIE_SECURE
   - X_FRAME_OPTIONS = 'DENY'
   - SECURE_HSTS_*

---

## Оптимизация

### Запросы к БД

- Использование `select_related()` для ForeignKey связей
- Использование `prefetch_related()` для обратных ForeignKey и ManyToMany
- Использование `values_list()` для получения только нужных полей
- Оптимизация запросов в views: home, detail, profile_view

### Примеры оптимизации:

```python
# Оптимизированный запрос постов
Post.objects.all().select_related('author').prefetch_related('likes', 'comments')

# Оптимизированный запрос комментариев
post.comments.select_related('author').order_by('created_at')
```

---

## Админ-панель

Все модели зарегистрированы в админ-панели с настройками:

- **PostAdmin:** список полей, фильтры, поиск, кастомные методы
- **LikeAdmin:** список полей, фильтры, поиск
- **CommentAdmin:** список полей, фильтры, поиск, превью текста
- **UserAdmin:** расширенная настройка с полями avatar и bio
- **FollowAdmin:** список полей, фильтры, поиск

---

## Переменные окружения

Файл `.env` (не в git):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Настройки email (опционально, для сброса пароля)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# Для продакшена:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password
# DEFAULT_FROM_EMAIL=noreply@minisocial.local
```

---

## Зависимости

Все зависимости указаны в `requirements.txt`:
- Django 4.2+
- Pillow (работа с изображениями)
- django-crispy-forms, crispy-bootstrap5 (формы)
- python-decouple (переменные окружения)
- whitenoise (статичные файлы в production)
- django-extensions (утилиты для разработки)
- python-dateutil (работа с датами)

---

## Развертывание

### Development

1. Установить зависимости
2. Создать `.env` файл
3. Выполнить миграции
4. Создать суперпользователя
5. Запустить `python manage.py runserver`

### Production

1. Установить `DEBUG=False` в `.env`
2. Настроить `ALLOWED_HOSTS`
3. Использовать PostgreSQL вместо SQLite
4. Настроить веб-сервер (Nginx + Gunicorn)
5. Настроить HTTPS
6. Выполнить `python manage.py collectstatic`
7. Настроить безопасный хостинг для медиа-файлов

---

## Возможные улучшения на будущее

### Функциональные улучшения
- Теги и хэштеги к постам
- Репосты постов
- Группы и сообщества
- Расширенные настройки уведомлений
- Поддержка видео и аудио контента
- Статусы пользователей

### Технические улучшения
- Кэширование (Redis)
- Миграция на PostgreSQL
- Фоновые задачи (Celery)
- REST/GraphQL API
- Unit и integration тесты
- CI/CD pipeline
- Мониторинг и логирование

### UX/UI улучшения
- Темная тема
- Real-time обновления (WebSockets)
- PWA поддержка
- Улучшенная мобильная версия
- Мультиязычность

Подробнее см. раздел "Возможные улучшения на будущее" в README.md
