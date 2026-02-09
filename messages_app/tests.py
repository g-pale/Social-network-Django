from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from messages_app.models import Conversation
from notifications.models import Notification


User = get_user_model()


class MessageNotificationTests(TestCase):
    def setUp(self):
        self.current_user = User.objects.create_user(
            username="user_a",
            email="user_a@example.com",
            password="StrongPass123!",
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            email="user_b@example.com",
            password="StrongPass123!",
        )
        self.user_c = User.objects.create_user(
            username="user_c",
            email="user_c@example.com",
            password="StrongPass123!",
        )

        self.conv_ab = Conversation.objects.create()
        self.conv_ab.participants.add(self.current_user, self.user_b)

        self.conv_ac = Conversation.objects.create()
        self.conv_ac.participants.add(self.current_user, self.user_c)

        self.notification_ab = Notification.objects.create(
            recipient=self.current_user,
            actor=self.user_b,
            notification_type="message",
            conversation=self.conv_ab,
            is_read=False,
        )
        self.notification_ac = Notification.objects.create(
            recipient=self.current_user,
            actor=self.user_c,
            notification_type="message",
            conversation=self.conv_ac,
            is_read=False,
        )

    def test_opening_conversation_marks_only_current_conversation_notifications_read(self):
        self.client.force_login(self.current_user)

        response = self.client.get(
            reverse("messages_app:conversation", kwargs={"conversation_id": self.conv_ab.id})
        )

        self.assertEqual(response.status_code, 200)
        self.notification_ab.refresh_from_db()
        self.notification_ac.refresh_from_db()
        self.assertTrue(self.notification_ab.is_read)
        self.assertFalse(self.notification_ac.is_read)
