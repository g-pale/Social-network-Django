// Обработка уведомлений

document.addEventListener('DOMContentLoaded', function() {
    // Отмечаем уведомление как прочитанное при клике
    const notificationItems = document.querySelectorAll('.notification-item[data-mark-read-url]');
    
    notificationItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const markReadUrl = this.getAttribute('data-mark-read-url');
            const notificationId = this.getAttribute('data-notification-id');
            
            if (markReadUrl && !this.classList.contains('read')) {
                // Отправляем AJAX запрос для отметки как прочитанного
                fetch(markReadUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Убираем класс непрочитанного
                        this.classList.remove('list-group-item-primary');
                        this.classList.add('read');
                        // Убираем бейдж "Новое"
                        const badge = this.querySelector('.badge');
                        if (badge) {
                            badge.remove();
                        }
                        // Убираем атрибут data-mark-read-url
                        this.removeAttribute('data-mark-read-url');
                        
                        // Обновляем счетчик уведомлений в навигации
                        updateNotificationCount();
                    }
                })
                .catch(error => {
                    console.error('Ошибка при отметке уведомления:', error);
                });
            }
        });
    });
    
    // Обновляем счетчик уведомлений каждые 30 секунд
    if (document.getElementById('notification-count')) {
        updateNotificationCount();
        setInterval(updateNotificationCount, 30000); // 30 секунд
    }
});

// Функция для обновления счетчика непрочитанных уведомлений
function updateNotificationCount() {
    fetch('/notifications/unread-count/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.json())
    .then(data => {
        const countElement = document.getElementById('notification-count');
        const badgeElement = document.getElementById('notification-badge');
        
        if (countElement) {
            if (data.count > 0) {
                countElement.textContent = data.count;
                if (badgeElement) {
                    badgeElement.style.display = 'inline-block';
                }
            } else {
                countElement.textContent = '0';
                if (badgeElement) {
                    badgeElement.style.display = 'none';
                }
            }
        }
    })
    .catch(error => {
        console.error('Ошибка при обновлении счетчика уведомлений:', error);
    });
}

// Функция для получения CSRF токена
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
