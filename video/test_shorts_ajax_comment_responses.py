from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Notification, Video
from .shorts_models import VideoShort


class ShortsAjaxCommentResponseTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="ajax-comment-creator", password="password123")
        self.viewer = User.objects.create_user(username="ajax-comment-viewer", password="password123")
        self.video = Video.objects.create(
            title="AJAX Comment Short",
            description="",
            thumbnail="videos/thumbnails/ajax-comment.jpg",
            video_file="videos/files/ajax-comment.mp4",
            author=self.creator,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)
        self.client.force_login(self.viewer)

    def test_ajax_comment_returns_created_comment_and_count(self):
        response = self.client.post(
            reverse("add_short_comment", args=[self.video.pk]),
            {"comment": "Comment without leaving the feed"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        comment = Comment.objects.get(video=self.video, author=self.viewer, parent__isnull=True)
        self.assertEqual(payload["id"], comment.pk)
        self.assertEqual(payload["author"], self.viewer.username)
        self.assertEqual(payload["comment"], "Comment without leaving the feed")
        self.assertEqual(payload["reply_url"], reverse("add_short_reply", args=[comment.pk]))
        self.assertEqual(payload["comment_count"], 1)

    def test_ajax_comment_preserves_creator_notification(self):
        self.client.post(
            reverse("add_short_comment", args=[self.video.pk]),
            {"comment": "Notify creator"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.creator,
                actor=self.viewer,
                video=self.video,
                kind=Notification.Kind.COMMENT,
            ).exists()
        )

    def test_ajax_invalid_comment_returns_validation_errors_without_creating_comment(self):
        response = self.client.post(
            reverse("add_short_comment", args=[self.video.pk]),
            {"comment": ""},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("errors", response.json())
        self.assertFalse(Comment.objects.filter(video=self.video, author=self.viewer).exists())

    def test_regular_post_keeps_existing_redirect_fallback(self):
        response = self.client.post(
            reverse("add_short_comment", args=[self.video.pk]),
            {"comment": "Fallback comment"},
        )
        self.assertRedirects(
            response,
            f"/videos/shorts/#short-{self.video.pk}",
            fetch_redirect_response=False,
        )
        self.assertTrue(Comment.objects.filter(video=self.video, author=self.viewer).exists())

    def test_ajax_comment_endpoint_still_rejects_standard_video(self):
        standard = Video.objects.create(
            title="Standard Video",
            description="",
            thumbnail="videos/thumbnails/standard-comment.jpg",
            video_file="videos/files/standard-comment.mp4",
            author=self.creator,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        response = self.client.post(
            reverse("add_short_comment", args=[standard.pk]),
            {"comment": "Should not work"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)
