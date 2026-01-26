// JavaScript для обработки комментариев через AJAX

document.addEventListener('DOMContentLoaded', function() {
    // Получаем CSRF токен из cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Обработчик формы создания комментария
    const commentForm = document.getElementById('comment-form');
    
    if (commentForm) {
        // Проверяем, не добавлен ли уже обработчик (защита от двойной загрузки скрипта)
        if (commentForm.dataset.listenerAdded === 'true') {
            return; // Обработчик уже добавлен
        }
        commentForm.dataset.listenerAdded = 'true';
        
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopPropagation(); // Останавливаем всплытие события
            
            // Защита от двойной отправки через data-атрибут формы
            if (this.dataset.processing === 'true') {
                return false;
            }
            
            const formData = new FormData(this);
            const postId = window.location.pathname.match(/\/(\d+)\//)?.[1];
            const submitButton = this.querySelector('button[type="submit"]');
            const textarea = this.querySelector('textarea');
            
            if (!postId) {
                alert('Ошибка: не удалось определить ID поста.');
                return false;
            }
            
            // Устанавливаем флаг обработки на форме
            this.dataset.processing = 'true';
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Отправка...';
            
            // Получаем CSRF токен
            const csrftoken = getCookie('csrftoken');
            
            // Отправляем AJAX запрос
            fetch(`/${postId}/comment/`, {  // URL соответствует posts:create_comment
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Ошибка сервера');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Очищаем форму
                textarea.value = '';
                
                // Скрываем сообщение "Пока нет комментариев"
                const noComments = document.getElementById('no-comments');
                if (noComments) {
                    noComments.style.display = 'none';
                }
                
                // Создаем HTML для нового комментария
                const avatarHtml = data.comment.avatar_url 
                    ? `<img src="${data.comment.avatar_url}" alt="${data.comment.author}" class="rounded-circle me-2" style="width: 32px; height: 32px; object-fit: cover;">`
                    : `<div class="rounded-circle bg-secondary text-white d-inline-flex align-items-center justify-content-center me-2" style="width: 32px; height: 32px; font-size: 14px;">${data.comment.author.charAt(0).toUpperCase()}</div>`;
                
                const commentHtml = `
                    <div class="mb-3 pb-3 comment-item border-bottom" data-comment-id="${data.comment.id}">
                        <div class="d-flex align-items-start">
                            ${avatarHtml}
                            <div class="flex-grow-1">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <strong>
                                            <a href="${data.comment.author_url}" class="text-decoration-none">
                                                ${data.comment.author}
                                            </a>
                                        </strong>
                                        <small class="text-muted ms-2">${data.comment.created_at}</small>
                                    </div>
                                    <button class="btn btn-sm btn-outline-danger delete-comment-btn" 
                                            data-comment-id="${data.comment.id}"
                                            title="Удалить комментарий">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </div>
                                <p class="mb-0 mt-1">${data.comment.text.replace(/\n/g, '<br>')}</p>
                            </div>
                        </div>
                    </div>
                `;
                
                // Добавляем комментарий в начало списка
                const commentsList = document.getElementById('comments-list');
                const firstComment = commentsList.querySelector('.comment-item');
                if (firstComment) {
                    firstComment.insertAdjacentHTML('beforebegin', commentHtml);
                } else {
                    commentsList.insertAdjacentHTML('beforeend', commentHtml);
                }
                
                // Обновляем счетчик комментариев
                const commentsCount = document.getElementById('comments-count');
                if (commentsCount) {
                    commentsCount.textContent = data.comments_count;
                }
                
                // Добавляем обработчик для новой кнопки удаления
                const newDeleteBtn = commentsList.querySelector(`[data-comment-id="${data.comment.id}"] .delete-comment-btn`);
                if (newDeleteBtn) {
                    newDeleteBtn.addEventListener('click', handleDeleteComment);
                }
                
                // Сбрасываем флаг и включаем кнопку обратно
                commentForm.dataset.processing = 'false';
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-send"></i> Отправить комментарий';
            })
            .catch(error => {
                console.error('Ошибка при создании комментария:', error);
                alert('Произошла ошибка: ' + error.message);
                // Сбрасываем флаг и включаем кнопку обратно
                commentForm.dataset.processing = 'false';
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-send"></i> Отправить комментарий';
            });
            
            return false; // Предотвращаем стандартную отправку формы
        });
    }
    
    // Обработчик удаления комментария
    function handleDeleteComment(e) {
        e.preventDefault();
        
        const commentId = this.getAttribute('data-comment-id');
        const commentItem = this.closest('.comment-item');
        const button = this;
        const commentText = commentItem.querySelector('p.mb-0') ? commentItem.querySelector('p.mb-0').textContent.trim() : '';
        
        // Показываем модальное окно
        const deleteCommentModal = document.getElementById('deleteCommentModal');
        const deleteCommentText = document.getElementById('deleteCommentText');
        const confirmDeleteBtn = document.getElementById('confirmDeleteComment');
        
        if (deleteCommentModal && deleteCommentText && confirmDeleteBtn) {
            deleteCommentText.textContent = commentText.length > 50 ? commentText.substring(0, 50) + '...' : commentText;
            
            // Удаляем старые обработчики и добавляем новый
            const newConfirmBtn = confirmDeleteBtn.cloneNode(true);
            confirmDeleteBtn.parentNode.replaceChild(newConfirmBtn, confirmDeleteBtn);
            
            // Показываем модальное окно
            const modal = new bootstrap.Modal(deleteCommentModal);
            modal.show();
            
            // Обработчик подтверждения удаления
            newConfirmBtn.addEventListener('click', function() {
                modal.hide();
                performDeleteComment(commentId, commentItem, button);
            });
        } else {
            // Fallback на confirm, если модальное окно не найдено
            if (!confirm('Вы уверены, что хотите удалить этот комментарий?')) {
                return;
            }
            performDeleteComment(commentId, commentItem, button);
        }
    }
    
    // Функция для выполнения удаления комментария
    function performDeleteComment(commentId, commentItem, button) {
        
        // Отключаем кнопку
        if (button) {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
        }
        
        // Получаем CSRF токен
        const csrftoken = getCookie('csrftoken');
        
        // Создаем FormData для отправки
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', csrftoken);
        
        // Отправляем AJAX запрос
        fetch(`/comment/${commentId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Ошибка сервера');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Удаляем элемент комментария из DOM
            if (commentItem) {
                commentItem.remove();
            }
            
            // Обновляем счетчик комментариев
            const commentsCount = document.getElementById('comments-count');
            if (commentsCount) {
                commentsCount.textContent = data.comments_count;
            }
            
            // Если комментариев не осталось, показываем сообщение
            const commentsList = document.getElementById('comments-list');
            const remainingComments = commentsList.querySelectorAll('.comment-item');
            if (remainingComments.length === 0) {
                const noComments = document.getElementById('no-comments');
                if (!noComments) {
                    commentsList.insertAdjacentHTML('beforeend', '<p class="text-muted text-center py-3" id="no-comments">Пока нет комментариев. Будьте первым!</p>');
                } else {
                    noComments.style.display = 'block';
                }
            }
        })
        .catch(error => {
            console.error('Ошибка при удалении комментария:', error);
            alert('Произошла ошибка: ' + error.message);
            button.disabled = false;
            button.innerHTML = '<i class="bi bi-trash"></i>';
        });
    }
    
    // Добавляем обработчики для всех кнопок удаления комментариев
    document.querySelectorAll('.delete-comment-btn').forEach(function(button) {
        button.addEventListener('click', handleDeleteComment);
    });
});
