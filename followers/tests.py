from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from followers.models import Follow


User = get_user_model()


class FollowToggleTests(TestCase):
    """Тесты для подписки/отписки"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123!"
        )
        self.user2 = User.objects.create_user(
            username="bob", email="bob@example.com", password="StrongPass123!"
        )

    def test_follow_user(self):
        """Подписка на пользователя"""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("followers:toggle_follow", kwargs={"username": self.user2.username}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_unfollow_user(self):
        """Отписка от пользователя"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("followers:toggle_follow", kwargs={"username": self.user2.username}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_cannot_follow_self(self):
        """Нельзя подписаться на себя"""
        self.client.force_login(self.user1)
        self.client.post(
            reverse("followers:toggle_follow", kwargs={"username": self.user1.username}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, following=self.user1).exists()
        )

    def test_duplicate_follow_prevented(self):
        """Дубль подписки не создаётся"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.client.force_login(self.user1)
        # Повторный POST — должен сработать как toggle (отписка)
        self.client.post(
            reverse("followers:toggle_follow", kwargs={"username": self.user2.username}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_follow_requires_auth(self):
        """Подписка требует авторизации"""
        response = self.client.post(
            reverse("followers:toggle_follow", kwargs={"username": self.user2.username}),
        )
        self.assertNotEqual(response.status_code, 200)

    def test_followers_list_view(self):
        """Страница подписчиков доступна"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("followers:followers_list", kwargs={"username": self.user2.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

    def test_following_list_view(self):
        """Страница подписок доступна"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("followers:following_list", kwargs={"username": self.user1.username})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user2.username)
