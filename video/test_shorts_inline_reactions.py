from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Notification, Video
from .shorts_models import VideoShort


class ShortsInlineReactionTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="reaction-owner", password="password123")
        self.viewer = User.objects.create_user(username="reaction-viewer", password="password123")
        self.short = Video.objects.create(
            title="Reaction Short",
            description="Short used to test inline reactions",
            thumbnail="videos/thumbnails/reaction-short.jpg",
            video_file="videos/files/reaction-short.mp4",
            author=self.creator,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.short)
        self.standard = Video.objects.create(
            title="Standard Video",
            description="Not a Short",
            thumbnail="videos/thumbnails/standard.jpg",
            video_file="videos/files/standard.mp4",
            author=self.creator,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        self.client.force_login(self.viewer)

    def test_like_short_adds_like_notifies_and_returns_to_same_short(self):
        response = self.client.post(reverse("like_short", args=[self.short.pk]))
        self.assertRedirects(response, f"/videos/shorts/#short-{self.short.pk}", fetch_redirect_response=False)
        self.assertTrue(self.short.likes.filter(pk=self.viewer.pk).exists())
        self.assertFalse(self.short.dislikes.filter(pk=self.viewer.pk).exists())
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.creator,
                actor=self.viewer,
                video=self.short,
                kind=Notification.Kind.LIKE,
            ).exists()
        )

    def test_like_short_toggles_off_without_duplicate_notification(self):
        self.short.likes.add(self.viewer)
        Notification.objects.create(
            recipient=self.creator,
            actor=self.viewer,
            video=self.short,
            kind=Notification.Kind.LIKE,
        )
        response = self.client.post(reverse("like_short", args=[self.short.pk]))
        self.assertRedirects(response, f"/videos/shorts/#short-{self.short.pk}", fetch_redirect_response=False)
        self.assertFalse(self.short.likes.filter(pk=self.viewer.pk).exists())
        self.assertEqual(Notification.objects.filter(kind=Notification.Kind.LIKE).count(), 1)

    def test_dislike_short_replaces_like(self):
        self.short.likes.add(self.viewer)
        response = self.client.post(reverse("dislike_short", args=[self.short.pk]))
        self.assertRedirects(response, f"/videos/shorts/#short-{self.short.pk}", fetch_redirect_response=False)
        self.assertFalse(self.short.likes.filter(pk=self.viewer.pk).exists())
        self.assertTrue(self.short.dislikes.filter(pk=self.viewer.pk).exists())

    def test_reaction_endpoints_reject_standard_videos(self):
        self.assertEqual(self.client.post(reverse("like_short", args=[self.standard.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("dislike_short", args=[self.standard.pk])).status_code, 404)

    def test_feed_renders_current_reaction_state_and_shorts_endpoints(self):
        self.short.likes.add(self.viewer)
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, reverse("like_short", args=[self.short.pk]))
        self.assertContains(response, reverse("dislike_short", args=[self.short.pk]))
        self.assertContains(response, 'aria-pressed="true">Like · 1</button>')
        self.assertContains(response, 'aria-pressed="false">Dislike · 0</button>')
