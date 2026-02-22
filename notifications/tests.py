from django.contrib.auth import get_user_model
from django.test import TestCase

from notifications.models import Notification
from notifications.utils import create_notification
from posts.models import Post


User = get_user_model()


class CreateNotificationTests(TestCase):
    """Тесты создания уведомлений"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123!"
        )
        self.user2 = User.objects.create_user(
            username="bob", email="bob@example.com", password="StrongPass123!"
        )
        self.post = Post.objects.create(author=self.user2, text="Test post")

    def test_create_like_notification(self):
        """Уведомление о лайке создаётся"""
        create_notification(
            recipient=self.user2,
            actor=self.user1,
            notification_type="like",
            post=self.post,
        )
        self.assertEqual(Notification.objects.count(), 1)
        n = Notification.objects.first()
        self.assertEqual(n.notification_type, "like")
        self.assertEqual(n.recipient, self.user2)
        self.assertEqual(n.actor, self.user1)

    def test_no_self_notification(self):
        """Уведомление не создаётся для себя"""
        create_notification(
            recipient=self.user1,
            actor=self.user1,
            notification_type="like",
            post=self.post,
        )
        self.assertEqual(Notification.objects.count(), 0)

    def test_follow_notification(self):
        """Уведомление о подписке"""
        create_notification(
            recipient=self.user2,
            actor=self.user1,
            notification_type="follow",
        )
        self.assertEqual(Notification.objects.count(), 1)


class NotificationViewTests(TestCase):
    """Тесты views уведомлений"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123!"
        )
        self.other = User.objects.create_user(
            username="bob", email="bob@example.com", password="StrongPass123!"
        )

    def test_notifications_list_requires_auth(self):
        """Список уведомлений требует авторизации"""
        response = self.client.get("/notifications/")
        self.assertNotEqual(response.status_code, 200)

    def test_notifications_list_loads(self):
        """Список уведомлений загружается"""
        self.client.force_login(self.user)
        response = self.client.get("/notifications/")
        self.assertEqual(response.status_code, 200)

    def test_mark_all_read(self):
        """Пометить все как прочитанные"""
        Notification.objects.create(
            recipient=self.user,
            actor=self.other,
            notification_type="follow",
        )
        self.client.force_login(self.user)
        self.client.post("/notifications/mark-all-read/")
        self.assertEqual(Notification.objects.filter(is_read=False).count(), 0)

    def test_unread_count_api(self):
        """API подсчёта непрочитанных"""
        Notification.objects.create(
            recipient=self.user,
            actor=self.other,
            notification_type="follow",
        )
        self.client.force_login(self.user)
        response = self.client.get(
            "/notifications/unread-count/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("count", response.json())
