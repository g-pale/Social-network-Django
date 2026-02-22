from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from messages_app.models import Conversation, Message


User = get_user_model()


class ConversationTests(TestCase):
    """Тесты бесед"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123!"
        )
        self.user2 = User.objects.create_user(
            username="bob", email="bob@example.com", password="StrongPass123!"
        )

    def test_start_conversation(self):
        """Начать новую беседу"""
        self.client.force_login(self.user1)
        self.client.get(
            reverse("messages_app:start_conversation", kwargs={"username": self.user2.username})
        )
        # Должен создать беседу и редиректнуть
        self.assertEqual(Conversation.objects.count(), 1)
        conv = Conversation.objects.first()
        self.assertIn(self.user1, conv.participants.all())
        self.assertIn(self.user2, conv.participants.all())

    def test_start_conversation_with_self_denied(self):
        """Нельзя начать беседу с самим собой"""
        self.client.force_login(self.user1)
        self.client.get(
            reverse("messages_app:start_conversation", kwargs={"username": self.user1.username})
        )
        self.assertEqual(Conversation.objects.count(), 0)

    def test_conversations_list_requires_auth(self):
        """Список бесед требует авторизации"""
        response = self.client.get(reverse("messages_app:conversations"))
        self.assertNotEqual(response.status_code, 200)

    def test_conversations_list_loads(self):
        """Список бесед загружается"""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("messages_app:conversations"))
        self.assertEqual(response.status_code, 200)


class MessageTests(TestCase):
    """Тесты сообщений"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123!"
        )
        self.user2 = User.objects.create_user(
            username="bob", email="bob@example.com", password="StrongPass123!"
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_send_message(self):
        """Отправка сообщения"""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("messages_app:conversation", kwargs={"conversation_id": self.conversation.pk}),
            data={"text": "Hello Bob!"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 1)
        msg = Message.objects.first()
        self.assertEqual(msg.text, "Hello Bob!")
        self.assertEqual(msg.sender, self.user1)

    def test_unread_messages_count(self):
        """Подсчёт непрочитанных сообщений"""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,
            text="Unread message",
        )
        count = self.conversation.get_unread_count(self.user1)
        self.assertEqual(count, 1)

    def test_conversation_detail_requires_auth(self):
        """Просмотр беседы требует авторизации"""
        response = self.client.get(
            reverse("messages_app:conversation", kwargs={"conversation_id": self.conversation.pk})
        )
        self.assertNotEqual(response.status_code, 200)

    def test_conversation_detail_loads(self):
        """Просмотр беседы работает для участника"""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("messages_app:conversation", kwargs={"conversation_id": self.conversation.pk})
        )
        self.assertEqual(response.status_code, 200)
