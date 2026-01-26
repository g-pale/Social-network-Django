// Обработка отправки сообщений

document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('message-form');
    const messagesContainer = document.getElementById('messages-container');
    const messagesList = document.getElementById('messages-list');
    const sendButton = document.getElementById('send-button');
    
    if (messageForm) {
        // Предотвращаем двойную отправку
        let isProcessing = false;
        
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (isProcessing) {
                return false;
            }
            
            const formData = new FormData(this);
            const messageText = formData.get('text').trim();
            
            if (!messageText) {
                return false;
            }
            
            isProcessing = true;
            sendButton.disabled = true;
            sendButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Отправка...';
            
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Добавляем новое сообщение в список
                    addMessageToDOM(data.message, true);
                    
                    // Очищаем форму
                    const textInput = this.querySelector('textarea[name="text"]');
                    if (textInput) {
                        textInput.value = '';
                    }
                    
                    // Прокручиваем вниз
                    scrollToBottom();
                } else {
                    alert('Ошибка при отправке сообщения: ' + (data.error || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Произошла ошибка при отправке сообщения');
            })
            .finally(() => {
                isProcessing = false;
                sendButton.disabled = false;
                sendButton.innerHTML = '<i class="bi bi-send"></i> Отправить';
            });
            
            return false;
        });
    }
    
    // Прокручиваем вниз при загрузке страницы
    if (messagesContainer) {
        scrollToBottom();
    }
    
    // Автоматическое обновление сообщений каждые 5 секунд
    if (messagesContainer) {
        setInterval(function() {
            updateMessages();
        }, 5000);
    }
});

// Функция для добавления сообщения в DOM
function addMessageToDOM(messageData, isOwn) {
    const messagesList = document.getElementById('messages-list');
    if (!messagesList) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `mb-3 ${isOwn ? 'text-end' : ''}`;
    
    const messageContent = `
        <div class="d-inline-block ${isOwn ? 'bg-primary text-white' : 'bg-light'} rounded p-2" 
             style="max-width: 70%;">
            <div class="d-flex align-items-start">
                ${!isOwn ? `
                    <div class="rounded-circle bg-secondary text-white d-inline-flex align-items-center justify-content-center me-2" 
                         style="width: 30px; height: 30px; font-size: 12px;">
                        ${messageData.sender.charAt(0).toUpperCase()}
                    </div>
                ` : ''}
                <div class="flex-grow-1">
                    ${!isOwn ? `<small class="d-block mb-1"><strong>${messageData.sender}</strong></small>` : ''}
                    <p class="mb-1">${escapeHtml(messageData.text).replace(/\n/g, '<br>')}</p>
                    <small class="text-muted">${messageData.created_at}</small>
                </div>
            </div>
        </div>
    `;
    
    messageDiv.innerHTML = messageContent;
    messagesList.appendChild(messageDiv);
    
    scrollToBottom();
}

// Функция для обновления сообщений
function updateMessages() {
    // Можно реализовать AJAX-запрос для получения новых сообщений
    // Пока оставляем пустым, так как это требует дополнительной логики на сервере
}

// Функция для прокрутки вниз
function scrollToBottom() {
    const messagesContainer = document.getElementById('messages-container');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Функция для экранирования HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
