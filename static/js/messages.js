// Обработка отправки сообщений

document.addEventListener('DOMContentLoaded', function () {
    const messageForm = document.getElementById('message-form');
    const messagesContainer = document.getElementById('messages-container');
    const messagesList = document.getElementById('messages-list');
    const sendButton = document.getElementById('send-button');

    if (messageForm) {
        // Предотвращаем двойную отправку
        let isProcessing = false;

        messageForm.addEventListener('submit', function (e) {
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
            sendButton.innerHTML = '<i class="bi bi-hourglass-split"></i>';

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
                            textInput.style.height = 'auto'; // Сброс высоты
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
                    sendButton.innerHTML = '<i class="bi bi-send-fill ms-1"></i>';
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
        setInterval(function () {
            updateMessages();
        }, 5000);
    }
});

// Функция для добавления сообщения в DOM
function addMessageToDOM(messageData, isOwn) {
    const messagesList = document.getElementById('messages-list');
    if (!messagesList) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `d-flex w-100 ${isOwn ? 'justify-content-end' : 'justify-content-start'}`;

    // Эскейпим текст и конвертируем переносы строк
    const safeText = escapeHtml(messageData.text).replace(/\n/g, '<br>');

    const messageContent = `
        <div class="message-bubble ${isOwn ? 'sent' : 'received shadow-sm'}">
            <!-- Текст сообщения -->
            <div class="mb-1" style="word-wrap: break-word; text-align: left;">
                ${safeText}
            </div>
            <!-- Время -->
            <div class="text-end" style="font-size: 0.7rem; opacity: 0.8;">
                ${messageData.created_at}
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

// getCookie и escapeHtml определены в utils.js
