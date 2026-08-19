from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Channel


GIF_1X1 = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
    b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)


class ProfileAndChannelCreationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator",
            password="password123",
            first_name="Test",
            last_name="Creator",
            email="creator@example.com",
        )

    def test_accounts_profile_redirects_to_current_user_profile(self):
        self.client.login(username="creator", password="password123")

        response = self.client.get(reverse("current_profile"))

        self.assertRedirects(
            response,
            reverse("user_profile", kwargs={"username": "creator"}),
        )

    def test_profile_requires_login_for_current_user_route(self):
        response = self.client.get(reverse("current_profile"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_authenticated_user_can_create_channel(self):
        self.client.login(username="creator", password="password123")
        thumbnail = SimpleUploadedFile(
            "channel.gif", GIF_1X1, content_type="image/gif"
        )

        response = self.client.post(
            reverse("channel_create"),
            {
                "name": "Creator Channel",
                "description": "My new channel",
                "thumbnail": thumbnail,
            },
        )

        channel = Channel.objects.get(name="Creator Channel")
        self.assertEqual(channel.owner, self.user)
        self.assertRedirects(
            response, reverse("channel_detail", kwargs={"pk": channel.pk})
        )

    def test_authenticated_user_can_create_channel_without_thumbnail(self):
        self.client.login(username="creator", password="password123")

        response = self.client.post(
            reverse("channel_create"),
            {
                "name": "Starter Channel",
                "description": "No artwork yet",
            },
        )

        channel = Channel.objects.get(name="Starter Channel")
        self.assertFalse(channel.thumbnail)
        self.assertRedirects(
            response, reverse("channel_detail", kwargs={"pk": channel.pk})
        )

        detail = self.client.get(reverse("channel_detail", kwargs={"pk": channel.pk}))
        self.assertContains(detail, "Starter Channel default channel avatar")
        self.assertContains(detail, "<span>S</span>", html=True)

    def test_channel_creation_requires_login(self):
        response = self.client.get(reverse("channel_create"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_upload_guides_user_without_channel_to_create_one(self):
        self.client.login(username="creator", password="password123")

        response = self.client.get(reverse("upload"))

        self.assertContains(response, "Create a channel first")
        self.assertContains(response, reverse("channel_create"))

    def test_profile_lists_owned_channels(self):
        Channel.objects.create(
            name="Creator Channel",
            description="My channel",
            thumbnail="channels/thumbnails/channel.jpg",
            owner=self.user,
        )

        response = self.client.get(
            reverse("user_profile", kwargs={"username": "creator"})
        )

        self.assertContains(response, "Creator Channel")
