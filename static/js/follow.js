// JavaScript для обработки подписок через AJAX

document.addEventListener('DOMContentLoaded', function() {
    // Обработчик для всех кнопок подписки
    document.querySelectorAll('.follow-btn').forEach(function(button) {
        // Проверяем, не добавлен ли уже обработчик
        if (button.dataset.listenerAdded === 'true') {
            return; // Обработчик уже добавлен
        }
        button.dataset.listenerAdded = 'true';
        
        let isProcessing = false; // Флаг для защиты от двойных кликов
        
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation(); // Останавливаем все обработчики
            
            // Защита от двойных кликов
            if (isProcessing) {
                return false;
            }
            
            // Дополнительная проверка через data-атрибут
            if (this.dataset.processing === 'true') {
                return false;
            }
            
            const username = this.getAttribute('data-username');
            const isFollowing = this.getAttribute('data-following') === 'true';
            const buttonElement = this;
            const followText = this.querySelector('.follow-text');
            const icon = this.querySelector('i');
            
            // Устанавливаем флаги и отключаем кнопку
            isProcessing = true;
            this.dataset.processing = 'true';
            this.disabled = true;
            const originalText = followText ? followText.textContent : '';
            if (followText) {
                followText.textContent = 'Обработка...';
            }
            if (icon) {
                icon.className = 'spinner-border spinner-border-sm';
            }
            
            // Получаем CSRF токен
            const csrftoken = getCookie('csrftoken');
            
            // Создаем FormData для отправки
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrftoken);
            
            // Отправляем AJAX запрос
            fetch(`/follow/toggle/${username}/`, {
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
                
                // Обновляем UI
                if (data.action === 'followed') {
                    // Подписка добавлена
                    buttonElement.setAttribute('data-following', 'true');
                    buttonElement.classList.remove('btn-primary');
                    buttonElement.classList.add('btn-outline-danger');
                    const newIcon = buttonElement.querySelector('i');
                    const newText = buttonElement.querySelector('.follow-text');
                    if (newIcon) {
                        newIcon.className = 'bi bi-person-dash';
                    }
                    if (newText) {
                        newText.textContent = 'Отписаться';
                    }
                } else if (data.action === 'unfollowed') {
                    // Подписка удалена
                    buttonElement.setAttribute('data-following', 'false');
                    buttonElement.classList.remove('btn-outline-danger');
                    buttonElement.classList.add('btn-primary');
                    const newIcon = buttonElement.querySelector('i');
                    const newText = buttonElement.querySelector('.follow-text');
                    if (newIcon) {
                        newIcon.className = 'bi bi-person-plus';
                    }
                    if (newText) {
                        newText.textContent = 'Подписаться';
                    }
                }
                
                // Обновляем счетчик подписчиков (если есть на странице)
                const followersCount = document.getElementById('followers-count');
                if (followersCount && data.followers_count !== undefined) {
                    followersCount.textContent = data.followers_count;
                }
                
                // Сбрасываем флаги и включаем кнопку обратно
                isProcessing = false;
                buttonElement.dataset.processing = 'false';
                buttonElement.disabled = false;
            })
            .catch(error => {
                console.error('Ошибка при обработке подписки:', error);
                // Показываем ошибку только если это не просто проблема с сетью
                if (error.message && !error.message.includes('Failed to fetch')) {
                    alert('Произошла ошибка: ' + error.message);
                }
                // Сбрасываем флаги и включаем кнопку обратно
                isProcessing = false;
                buttonElement.dataset.processing = 'false';
                buttonElement.disabled = false;
                if (followText) {
                    followText.textContent = originalText;
                }
                if (icon) {
                    icon.className = isFollowing ? 'bi bi-person-dash' : 'bi bi-person-plus';
                }
            });
            
            return false;
        });
    });
});
