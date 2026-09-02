from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsAjaxReactionTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="ajax-creator", password="password123")
        self.viewer = User.objects.create_user(username="ajax-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="AJAX Channel", description="")
        self.video = Video.objects.create(
            title="AJAX Short",
            description="",
            thumbnail="videos/thumbnails/ajax.jpg",
            video_file="videos/files/ajax.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)
        self.client.force_login(self.viewer)

    def test_ajax_like_returns_updated_state_without_redirect(self):
        response = self.client.post(
            reverse("like_short", args=[self.video.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"liked": True, "disliked": False, "like_count": 1, "dislike_count": 0})
        self.assertTrue(self.video.likes.filter(pk=self.viewer.pk).exists())

    def test_ajax_dislike_replaces_like_and_returns_counts(self):
        self.video.likes.add(self.viewer)
        response = self.client.post(
            reverse("dislike_short", args=[self.video.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"liked": False, "disliked": True, "like_count": 0, "dislike_count": 1})

    def test_regular_post_keeps_non_javascript_redirect_fallback(self):
        response = self.client.post(reverse("like_short", args=[self.video.pk]))
        self.assertRedirects(response, f"/videos/shorts/#short-{self.video.pk}", fetch_redirect_response=False)

    def test_feed_contains_ajax_reaction_hooks_and_error_surface(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, 'data-short-reaction-form data-reaction="like"')
        self.assertContains(response, 'data-short-reaction-form data-reaction="dislike"')
        self.assertContains(response, "data-short-like")
        self.assertContains(response, "data-short-dislike")
        self.assertContains(response, "data-short-reaction-error")
        script = Path("video/static/video/shorts_reaction_ajax.js").read_text(encoding="utf-8")
        self.assertIn("X-Requested-With", script)
        self.assertIn("XMLHttpRequest", script)
