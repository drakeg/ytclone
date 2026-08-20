import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel, Video


class UnlistedSharingTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        category = Category.objects.create(name="General", description="General", thumbnail="categories/general.jpg")
        channel = Channel.objects.create(name="Channel", description="Channel", thumbnail="channels/channel.jpg", owner=self.creator)
        self.video = Video.objects.create(title="Secret link video", description="Secret", thumbnail="videos/secret.jpg", video_file="videos/files/secret.mp4", author=self.creator, channel=channel, category=category, publication_status=Video.PublicationStatus.UNLISTED)

    def shared_url(self, token=None):
        return reverse("shared_video_detail", kwargs={"token": token or self.video.share_token})

    def test_valid_share_link_is_public_but_normal_url_is_owner_only(self):
        self.assertEqual(self.client.get(self.shared_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse("video_detail", kwargs={"pk": self.video.pk})).status_code, 404)
        self.client.login(username="creator", password="password123")
        self.assertEqual(self.client.get(reverse("video_detail", kwargs={"pk": self.video.pk})).status_code, 200)

    def test_invalid_token_returns_404(self):
        self.assertEqual(self.client.get(self.shared_url(uuid.uuid4())).status_code, 404)

    def test_token_does_not_open_draft_or_scheduled_video(self):
        for status in [Video.PublicationStatus.DRAFT, Video.PublicationStatus.SCHEDULED]:
            self.video.publication_status = status
            self.video.save(update_fields=["publication_status"])
            self.assertEqual(self.client.get(self.shared_url()).status_code, 404)

    def test_owner_can_rotate_token_and_old_link_is_revoked(self):
        old_token = self.video.share_token
        self.client.login(username="creator", password="password123")
        response = self.client.post(reverse("video_rotate_share_token", kwargs={"pk": self.video.pk}))
        self.assertRedirects(response, reverse("video_detail", kwargs={"pk": self.video.pk}))
        self.video.refresh_from_db()
        self.assertNotEqual(self.video.share_token, old_token)
        self.client.logout()
        self.assertEqual(self.client.get(self.shared_url(old_token)).status_code, 404)
        self.assertEqual(self.client.get(self.shared_url()).status_code, 200)

    @patch("video.access_views.serve", return_value=HttpResponse("media"))
    def test_rotating_share_token_revokes_existing_direct_media_grant(self, unused_serve):
        media_url = reverse("protected_video_media", kwargs={"path": "secret.mp4"})

        self.assertEqual(self.client.get(self.shared_url()).status_code, 200)
        self.assertEqual(self.client.get(media_url).status_code, 200)

        self.video.share_token = uuid.uuid4()
        self.video.save(update_fields=["share_token"])

        self.assertEqual(self.client.get(media_url).status_code, 404)
        self.assertEqual(self.client.get(self.shared_url()).status_code, 200)
        self.assertEqual(self.client.get(media_url).status_code, 200)

    def test_non_owner_cannot_rotate_and_get_is_rejected(self):
        url = reverse("video_rotate_share_token", kwargs={"pk": self.video.pk})
        self.client.login(username="viewer", password="password123")
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.logout()
        self.client.login(username="creator", password="password123")
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_unlisted_video_is_absent_from_public_surfaces(self):
        urls = [
            reverse("video_list"),
            reverse("search") + "?query=Secret",
            reverse("channel_detail", kwargs={"pk": self.video.channel.pk}),
            reverse("category_detail", kwargs={"pk": self.video.category.pk}),
            reverse("user_profile", kwargs={"username": self.creator.username}),
        ]
        for url in urls:
            self.assertNotContains(self.client.get(url), self.video.title)

    def test_owner_sees_share_controls(self):
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("video_detail", kwargs={"pk": self.video.pk}))
        self.assertContains(response, self.shared_url())
        self.assertContains(response, "Revoke and create a new link")
