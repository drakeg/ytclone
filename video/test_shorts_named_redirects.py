from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Comment, Video
from .shorts_models import VideoShort


class ShortsNamedRedirectTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="redirect-creator", password="password123")
        self.viewer = User.objects.create_user(username="redirect-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Redirect Channel", description="")
        self.video = Video.objects.create(
            title="Redirect Short",
            description="Named redirect coverage",
            thumbnail="videos/thumbnails/redirect.jpg",
            video_file="videos/files/redirect.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)
        self.parent = Comment.objects.create(video=self.video, author=self.creator, comment="Parent")
        self.client.force_login(self.viewer)
        self.expected = f'{reverse("shorts_feed")}#short-{self.video.pk}'

    def test_like_fallback_uses_shorts_feed_route(self):
        response = self.client.post(reverse("like_short", args=[self.video.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.expected)

    def test_dislike_fallback_uses_shorts_feed_route(self):
        response = self.client.post(reverse("dislike_short", args=[self.video.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.expected)

    def test_comment_fallback_uses_shorts_feed_route(self):
        response = self.client.post(
            reverse("add_short_comment", args=[self.video.pk]),
            {"comment": "Comment"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.expected)

    def test_reply_fallback_uses_shorts_feed_route(self):
        response = self.client.post(
            reverse("add_short_reply", args=[self.parent.pk]),
            {"comment": "Reply"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.expected)
