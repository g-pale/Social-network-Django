// Обработка отправки сообщений через WebSockets

document.addEventListener('DOMContentLoaded', function () {
    const messageForm = document.getElementById('message-form');
    const messagesContainer = document.getElementById('messages-container');
    const sendButton = document.getElementById('send-button');
    const chatData = document.getElementById('chat-data');

    // Прокручиваем вниз при загрузке страницы
    if (messagesContainer) {
        scrollToBottom();
    }

    if (chatData && messageForm) {
        const conversationId = chatData.dataset.conversationId;
        const currentUserId = parseInt(chatData.dataset.currentUserId);

        const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const chatSocket = new WebSocket(
            wsProtocol + '//' + window.location.host + '/ws/chat/' + conversationId + '/'
        );

        chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            const message = data.message;
            const isOwn = (message.sender_id === currentUserId);

            addMessageToDOM(message, isOwn);

            // Если кнопка была 'disabled' из-за отправки
            sendButton.disabled = false;
            sendButton.innerHTML = '<i class="bi bi-send-fill ms-1"></i>';
        };

        chatSocket.onclose = function (e) {
            console.error('Chat socket closed unexpectedly');
        };

        messageForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const textInput = this.querySelector('textarea[name="text"]');
            const messageText = textInput.value.trim();

            if (!messageText) {
                return false;
            }

            // Отправляем сообщение по WebSocket
            chatSocket.send(JSON.stringify({
                'message': messageText
            }));

            // Визуальная блокировка до получения подтверждения
            sendButton.disabled = true;
            sendButton.innerHTML = '<i class="bi bi-hourglass-split"></i>';

            // Сбрасываем поле
            textInput.value = '';
            textInput.style.height = 'auto';

            return false;
        });
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

// Функция для прокрутки вниз
function scrollToBottom() {
    const messagesContainer = document.getElementById('messages-container');
    if (messagesContainer) {
        // Небольшая задержка, чтобы DOM успел обновиться
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 10);
    }
}
