import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        # Проверяем, есть ли доступ к беседе
        has_access = await self.check_conversation_access(self.conversation_id, self.user)
        if not has_access:
            await self.close()
            return

        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Покидаем группу
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Получение сообщения от WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json.get('message', '').strip()

        if not message_text:
            return

        # Сохранение сообщения в БД
        message = await self.save_message(self.user, self.conversation_id, message_text)

        avatar_url = message.sender.avatar.url if message.sender.avatar else None

        # Отправка сообщения группе (включая автора)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message.text,
                'sender_id': message.sender.id,
                'sender_username': message.sender.username,
                'avatar_url': avatar_url,
                'created_at': message.created_at.strftime('%H:%M')
            }
        )

    # Получение сообщения от group_send
    async def chat_message(self, event):
        # Отправка сообщения обратно клиенту по WebSocket
        await self.send(text_data=json.dumps({
            'message': {
                'text': event['message'],
                'sender_id': event['sender_id'],
                'sender': event['sender_username'],
                'avatar_url': event['avatar_url'],
                'created_at': event['created_at'],
            }
        }))

    @database_sync_to_async
    def check_conversation_access(self, conversation_id, user):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, conversation_id, text):
        conversation = Conversation.objects.get(id=conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            text=text
        )
        return message
