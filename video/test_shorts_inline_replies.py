from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Comment, Notification, Video
from .shorts_models import VideoShort


class ShortsInlineReplyTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="reply-owner", password="password123")
        self.viewer = User.objects.create_user(username="reply-viewer", password="password123")
        self.replier = User.objects.create_user(username="reply-user", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Reply Channel", description="")
        self.short = Video.objects.create(
            title="Reply Short",
            description="Short used to test inline replies",
            thumbnail="videos/thumbnails/reply-short.jpg",
            video_file="videos/files/reply-short.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.short)
        self.comment = Comment.objects.create(video=self.short, author=self.viewer, comment="Top-level comment")

    def test_feed_renders_recent_visible_replies(self):
        Comment.objects.create(video=self.short, author=self.replier, parent=self.comment, comment="First reply")
        Comment.objects.create(video=self.short, author=self.creator, parent=self.comment, comment="Second reply")
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "First reply")
        self.assertContains(response, "Second reply")
        self.assertContains(response, "2 replies")

    def test_hidden_reply_is_not_rendered_or_counted(self):
        Comment.objects.create(video=self.short, author=self.replier, parent=self.comment, comment="Visible reply")
        Comment.objects.create(video=self.short, author=self.creator, parent=self.comment, comment="Hidden reply", is_hidden=True)
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "Visible reply")
        self.assertNotContains(response, "Hidden reply")
        self.assertContains(response, "1 reply")

    def test_authenticated_viewer_sees_reply_form(self):
        self.client.force_login(self.replier)
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, reverse("add_short_reply", args=[self.comment.pk]))
        self.assertContains(response, "Post reply")

    def test_posting_reply_returns_to_same_short_and_notifies(self):
        self.client.force_login(self.replier)
        response = self.client.post(
            reverse("add_short_reply", args=[self.comment.pk]),
            {"comment": "Inline reply"},
        )
        self.assertRedirects(
            response,
            reverse("shorts_feed") + f"#short-{self.short.pk}",
            fetch_redirect_response=False,
        )
        reply = Comment.objects.get(parent=self.comment, author=self.replier)
        self.assertEqual(reply.comment, "Inline reply")
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.creator,
                actor=self.replier,
                kind=Notification.Kind.COMMENT,
                video=self.short,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.viewer,
                actor=self.replier,
                kind=Notification.Kind.REPLY,
                video=self.short,
            ).exists()
        )

    def test_reply_endpoint_rejects_hidden_parent(self):
        self.comment.is_hidden = True
        self.comment.save(update_fields=["is_hidden"])
        self.client.force_login(self.replier)
        response = self.client.post(
            reverse("add_short_reply", args=[self.comment.pk]),
            {"comment": "Should not post"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Comment.objects.filter(parent=self.comment).exists())

    def test_reply_endpoint_rejects_non_short_comment(self):
        standard = Video.objects.create(
            title="Standard video",
            description="",
            thumbnail="videos/thumbnails/standard.jpg",
            video_file="videos/files/standard.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        standard_comment = Comment.objects.create(video=standard, author=self.viewer, comment="Standard comment")
        self.client.force_login(self.replier)
        response = self.client.post(
            reverse("add_short_reply", args=[standard_comment.pk]),
            {"comment": "Should not post"},
        )
        self.assertEqual(response.status_code, 404)
