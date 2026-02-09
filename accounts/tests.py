from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class LoginSecurityTests(TestCase):
    def setUp(self):
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password=self.password,
        )

    def test_login_rejects_external_next_url(self):
        response = self.client.post(
            f"{reverse('accounts:login')}?next=https://evil.example/phish",
            data={"username": self.user.username, "password": self.password},
        )

        self.assertRedirects(response, reverse("posts:home"))

    def test_login_allows_local_next_url(self):
        response = self.client.post(
            f"{reverse('accounts:login')}?next={reverse('accounts:users_list')}",
            data={"username": self.user.username, "password": self.password},
        )

        self.assertRedirects(response, reverse("accounts:users_list"))


class LogoutMethodTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="StrongPass123!",
        )

    def test_logout_rejects_get(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("accounts:logout"))

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_accepts_post(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:logout"))

        self.assertRedirects(response, reverse("posts:home"))
        self.assertNotIn("_auth_user_id", self.client.session)
