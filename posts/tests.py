from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from posts.models import Post


User = get_user_model()


class PostOwnershipTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username="author",
            email="author@example.com",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            username="intruder",
            email="intruder@example.com",
            password="StrongPass123!",
        )
        self.post = Post.objects.create(author=self.author, text="Original post text")

    def test_non_author_cannot_edit_post(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("posts:edit", kwargs={"pk": self.post.pk}),
            data={"text": "Hacked text"},
        )

        self.assertRedirects(response, reverse("posts:detail", kwargs={"pk": self.post.pk}))
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, "Original post text")

    def test_non_author_cannot_delete_post(self):
        self.client.force_login(self.other_user)

        response = self.client.post(reverse("posts:delete", kwargs={"pk": self.post.pk}))

        self.assertRedirects(response, reverse("posts:detail", kwargs={"pk": self.post.pk}))
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
