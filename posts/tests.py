from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from posts.models import Post, Like, Comment


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


class PostCreateTests(TestCase):
    """Тесты создания постов"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="poster", email="poster@example.com", password="StrongPass123!"
        )

    def test_create_post(self):
        """Создание поста"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("posts:create"),
            data={"text": "Мой новый пост"},
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, "Мой новый пост")
        self.assertEqual(post.author, self.user)

    def test_create_post_requires_auth(self):
        """Создание поста требует авторизации"""
        response = self.client.post(
            reverse("posts:create"),
            data={"text": "Unauthorized post"},
        )
        self.assertEqual(Post.objects.count(), 0)

    def test_create_post_empty_text(self):
        """Пустой текст отклоняется"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("posts:create"),
            data={"text": "   "},
        )
        self.assertEqual(Post.objects.count(), 0)


class LikeTests(TestCase):
    """Тесты лайков"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="liker", email="liker@example.com", password="StrongPass123!"
        )
        self.author = User.objects.create_user(
            username="author", email="author@example.com", password="StrongPass123!"
        )
        self.post = Post.objects.create(author=self.author, text="Test post")

    def test_like_post(self):
        """Лайк поста"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("posts:toggle_like", kwargs={"pk": self.post.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Like.objects.filter(user=self.user, post=self.post).exists())

    def test_unlike_post(self):
        """Отмена лайка"""
        Like.objects.create(user=self.user, post=self.post)
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("posts:toggle_like", kwargs={"pk": self.post.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Like.objects.filter(user=self.user, post=self.post).exists())

    def test_cannot_like_own_post(self):
        """Нельзя лайкать свой пост"""
        self.client.force_login(self.author)
        response = self.client.post(
            reverse("posts:toggle_like", kwargs={"pk": self.post.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertFalse(Like.objects.filter(user=self.author, post=self.post).exists())


class CommentTests(TestCase):
    """Тесты комментариев"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="commenter", email="commenter@example.com", password="StrongPass123!"
        )
        self.author = User.objects.create_user(
            username="author", email="author@example.com", password="StrongPass123!"
        )
        self.post = Post.objects.create(author=self.author, text="Test post")

    def test_create_comment(self):
        """Создание комментария"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("posts:create_comment", kwargs={"pk": self.post.pk}),
            data={"text": "Отличный пост!"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)

    def test_delete_own_comment(self):
        """Удаление своего комментария"""
        comment = Comment.objects.create(
            post=self.post, author=self.user, text="To delete"
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("posts:delete_comment", kwargs={"pk": comment.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_cannot_delete_other_comment(self):
        """Нельзя удалить чужой комментарий"""
        comment = Comment.objects.create(
            post=self.post, author=self.author, text="Author comment"
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("posts:delete_comment", kwargs={"pk": comment.pk}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())


class HomeViewTests(TestCase):
    """Тесты главной страницы"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="viewer", email="viewer@example.com", password="StrongPass123!"
        )
        self.author = User.objects.create_user(
            username="author", email="author@example.com", password="StrongPass123!"
        )

    def test_home_page_loads(self):
        """Главная страница загружается"""
        response = self.client.get(reverse("posts:home"))
        self.assertEqual(response.status_code, 200)

    def test_home_page_shows_posts(self):
        """Главная страница показывает посты"""
        Post.objects.create(author=self.author, text="Visible post")
        response = self.client.get(reverse("posts:home"))
        self.assertContains(response, "Visible post")

    def test_home_page_filter_following(self):
        """Фильтр по подпискам"""
        from followers.models import Follow
        Follow.objects.create(follower=self.user, following=self.author)
        Post.objects.create(author=self.author, text="Followed post")
        self.client.force_login(self.user)
        response = self.client.get(reverse("posts:home") + "?filter=following")
        self.assertContains(response, "Followed post")
