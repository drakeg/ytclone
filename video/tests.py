from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel, Comment, Video


class SecurityAuthorizationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.other_user = User.objects.create_user(
            username="other", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General videos",
            thumbnail="categories/thumbnails/general.jpg",
        )
        self.video = Video.objects.create(
            title="Test video",
            description="A test video",
            thumbnail="videos/thumbnails/test.jpg",
            video_file="videos/files/test.mp4",
            author=self.owner,
            category=self.category,
        )
        self.channel = Channel.objects.create(
            name="Owner channel",
            description="Test channel",
            thumbnail="channels/thumbnails/test.jpg",
            owner=self.owner,
        )

    def test_profile_pages_are_public(self):
        response = self.client.get(
            reverse("user_profile", kwargs={"username": self.owner.username})
        )
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_cannot_upload(self):
        response = self.client.get(reverse("upload"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_user_cannot_edit_another_profile(self):
        self.client.login(username="other", password="password123")
        response = self.client.get(
            reverse("edit_profile", kwargs={"username": self.owner.username})
        )
        self.assertEqual(response.status_code, 404)

    def test_user_can_edit_own_profile(self):
        self.client.login(username="owner", password="password123")
        response = self.client.post(
            reverse("edit_profile", kwargs={"username": self.owner.username}),
            {
                "first_name": "Updated",
                "last_name": "Owner",
                "email": "owner@example.com",
            },
        )
        self.assertRedirects(
            response,
            reverse("user_profile", kwargs={"username": self.owner.username}),
        )
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.first_name, "Updated")

    def test_anonymous_user_cannot_create_comment(self):
        response = self.client.post(
            reverse("add_comment", kwargs={"pk": self.video.pk}),
            {"comment": "Anonymous comment"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)

    def test_authenticated_comment_records_author(self):
        self.client.login(username="other", password="password123")
        response = self.client.post(
            reverse("add_comment", kwargs={"pk": self.video.pk}),
            {"comment": "A real comment"},
        )
        self.assertRedirects(
            response, reverse("video_detail", kwargs={"pk": self.video.pk})
        )
        comment = Comment.objects.get()
        self.assertEqual(comment.author, self.other_user)
        self.assertEqual(comment.video, self.video)

    def test_comment_endpoint_rejects_get(self):
        self.client.login(username="other", password="password123")
        response = self.client.get(
            reverse("add_comment", kwargs={"pk": self.video.pk})
        )
        self.assertEqual(response.status_code, 405)

    def test_like_endpoint_requires_post(self):
        self.client.login(username="other", password="password123")
        response = self.client.get(
            reverse("like_video", kwargs={"pk": self.video.pk})
        )
        self.assertEqual(response.status_code, 405)
        self.assertFalse(self.video.likes.filter(pk=self.other_user.pk).exists())

    def test_dislike_endpoint_requires_post(self):
        self.client.login(username="other", password="password123")
        response = self.client.get(
            reverse("dislike_video", kwargs={"pk": self.video.pk})
        )
        self.assertEqual(response.status_code, 405)
        self.assertFalse(self.video.dislikes.filter(pk=self.other_user.pk).exists())

    def test_subscribe_endpoint_requires_post(self):
        self.client.login(username="other", password="password123")
        response = self.client.get(
            reverse("subscribe", kwargs={"pk": self.channel.pk})
        )
        self.assertEqual(response.status_code, 405)
        self.assertFalse(
            self.channel.subscribers.filter(pk=self.other_user.pk).exists()
        )

    def test_authenticated_post_can_like_and_subscribe(self):
        self.client.login(username="other", password="password123")
        like_response = self.client.post(
            reverse("like_video", kwargs={"pk": self.video.pk})
        )
        subscribe_response = self.client.post(
            reverse("subscribe", kwargs={"pk": self.channel.pk})
        )

        self.assertEqual(like_response.status_code, 302)
        self.assertEqual(subscribe_response.status_code, 302)
        self.assertTrue(self.video.likes.filter(pk=self.other_user.pk).exists())
        self.assertTrue(
            self.channel.subscribers.filter(pk=self.other_user.pk).exists()
        )
