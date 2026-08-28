from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Comment, Video
from .shorts_models import VideoShort


class ShortsInlineCommentsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="comment-owner", password="password123")
        self.viewer = User.objects.create_user(username="comment-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Comments Channel", description="")
        self.short = Video.objects.create(title="Comment Short", description="Test", thumbnail="videos/thumbnails/comment.jpg", video_file="videos/files/comment.mp4", author=self.creator, channel=self.channel, publication_status=Video.PublicationStatus.PUBLISHED)
        VideoShort.objects.create(video=self.short)

    def test_feed_shows_recent_visible_comments_and_count(self):
        Comment.objects.create(video=self.short, author=self.viewer, comment="Newest visible comment")
        Comment.objects.create(video=self.short, author=self.viewer, comment="Hidden comment", is_hidden=True)
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "Newest visible comment")
        self.assertNotContains(response, "Hidden comment")
        self.assertEqual(response.context["shorts"][0].shorts_comment_count, 1)

    def test_authenticated_viewer_can_comment_without_leaving_short_feed(self):
        self.client.force_login(self.viewer)
        response = self.client.post(reverse("add_short_comment", args=[self.short.pk]), {"comment": "Inline comment"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith(f"/videos/shorts/#short-{self.short.pk}"))
        self.assertTrue(Comment.objects.filter(video=self.short, author=self.viewer, comment="Inline comment").exists())

    def test_inline_comment_endpoint_rejects_standard_video(self):
        standard = Video.objects.create(title="Standard", description="Test", thumbnail="videos/thumbnails/standard.jpg", video_file="videos/files/standard.mp4", author=self.creator, channel=self.channel, publication_status=Video.PublicationStatus.PUBLISHED)
        self.client.force_login(self.viewer)
        response = self.client.post(reverse("add_short_comment", args=[standard.pk]), {"comment": "Nope"})
        self.assertEqual(response.status_code, 404)

    def test_anonymous_feed_offers_login_instead_of_comment_form(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "Log in to comment")
        self.assertNotContains(response, reverse("add_short_comment", args=[self.short.pk]))
