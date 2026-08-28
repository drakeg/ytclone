from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Comment, Video
from .shorts_models import VideoShort


class ShortsAjaxReplyResponseTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="reply-creator", password="password123")
        self.viewer = User.objects.create_user(username="reply-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Reply Channel", description="")
        self.video = Video.objects.create(
            title="Reply Short",
            description="AJAX reply test",
            thumbnail="videos/thumbnails/reply.jpg",
            video_file="videos/files/reply.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)
        self.parent = Comment.objects.create(video=self.video, author=self.creator, comment="Parent comment")
        self.client.force_login(self.viewer)

    def test_ajax_reply_returns_saved_reply_and_authoritative_count(self):
        response = self.client.post(
            reverse("add_short_reply", args=[self.parent.pk]),
            {"comment": "A new reply"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 201)
        reply = Comment.objects.get(parent=self.parent, author=self.viewer)
        self.assertEqual(
            response.json(),
            {
                "id": reply.pk,
                "parent_id": self.parent.pk,
                "author": self.viewer.username,
                "comment": "A new reply",
                "reply_count": 1,
            },
        )

    def test_ajax_invalid_reply_returns_validation_errors(self):
        response = self.client.post(
            reverse("add_short_reply", args=[self.parent.pk]),
            {"comment": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("comment", response.json()["errors"])
        self.assertFalse(Comment.objects.filter(parent=self.parent).exists())

    def test_regular_post_still_redirects_to_same_short(self):
        response = self.client.post(
            reverse("add_short_reply", args=[self.parent.pk]),
            {"comment": "Fallback reply"},
        )
        self.assertRedirects(
            response,
            f'{reverse("shorts_feed")}#short-{self.video.pk}',
            fetch_redirect_response=False,
        )

    def test_reply_to_reply_is_rejected(self):
        reply = Comment.objects.create(
            video=self.video,
            author=self.viewer,
            parent=self.parent,
            comment="Existing reply",
        )
        response = self.client.post(
            reverse("add_short_reply", args=[reply.pk]),
            {"comment": "Nested reply"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Comment.objects.filter(parent=reply).exists())
