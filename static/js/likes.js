// JavaScript для обработки лайков через AJAX

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
    
            // Обработчик для всех кнопок лайков
    document.querySelectorAll('.like-btn').forEach(function(button) {
        let isProcessing = false; // Флаг для защиты от двойных кликов
        
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Защита от двойных кликов
            if (isProcessing) {
                return;
            }
            
            const postId = this.getAttribute('data-post-id');
            const likesCountSpan = this.querySelector('.likes-count');
            const heartIcon = this.querySelector('i');
            const buttonElement = this;
            
            // Устанавливаем флаг и отключаем кнопку
            isProcessing = true;
            this.disabled = true;
            
            // Получаем CSRF токен
            const csrftoken = getCookie('csrftoken');
            
            // Создаем FormData для отправки (Django ожидает form data, а не JSON)
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrftoken);
            
            // Отправляем AJAX запрос
            fetch(`/${postId}/like/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData,
                credentials: 'same-origin'
            })
            .then(response => {
                // Проверяем статус ответа
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Ошибка сервера');
                    });
                }
                return response.json();
            })
            .then(data => {
                // Проверяем, есть ли ошибка в ответе
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Проверяем, что ответ валидный
                if (!data || !data.action) {
                    throw new Error('Неверный формат ответа от сервера');
                }
                
                // Обновляем UI
                if (data.action === 'liked') {
                    // Лайк добавлен
                    buttonElement.setAttribute('data-liked', 'true');
                    buttonElement.classList.remove('btn-outline-danger');
                    buttonElement.classList.add('btn-danger');
                    if (heartIcon) {
                        heartIcon.classList.remove('bi-heart');
                        heartIcon.classList.add('bi-heart-fill');
                    }
                } else if (data.action === 'unliked') {
                    // Лайк удален
                    buttonElement.setAttribute('data-liked', 'false');
                    buttonElement.classList.remove('btn-danger');
                    buttonElement.classList.add('btn-outline-danger');
                    if (heartIcon) {
                        heartIcon.classList.remove('bi-heart-fill');
                        heartIcon.classList.add('bi-heart');
                    }
                }
                
                // Обновляем счетчик лайков
                if (likesCountSpan) {
                    likesCountSpan.textContent = data.likes_count || 0;
                }
                
                // Сбрасываем флаг и включаем кнопку обратно
                isProcessing = false;
                buttonElement.disabled = false;
            })
            .catch(error => {
                console.error('Ошибка при обработке лайка:', error);
                // Показываем ошибку только если это реальная ошибка
                // Не показываем ошибку если это просто проблема с парсингом успешного ответа
                if (error.message && error.message.includes('Неверный формат')) {
                    // Это может быть проблема с ответом, но не критичная
                    console.warn('Предупреждение:', error.message);
                } else if (error.message && !error.message.includes('JSON')) {
                    // Показываем только реальные ошибки
                    alert('Произошла ошибка: ' + error.message);
                }
                // Сбрасываем флаг и включаем кнопку обратно
                isProcessing = false;
                buttonElement.disabled = false;
            });
        });
    });
});
