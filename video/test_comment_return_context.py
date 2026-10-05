from urllib.parse import quote

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Video


class CommentReturnContextTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="return-creator",
            password="password123",
        )
        self.viewer = User.objects.create_user(
            username="return-viewer",
            password="password123",
        )
        self.video = Video.objects.create(
            title="Return context video",
            description="Return context coverage",
            thumbnail="videos/return-context.jpg",
            video_file="videos/return-context.mp4",
            author=self.creator,
        )
        self.parent = Comment.objects.create(
            video=self.video,
            author=self.creator,
            comment="Parent for return context",
        )
        self.reply = Comment.objects.create(
            video=self.video,
            author=self.viewer,
            parent=self.parent,
            comment="Reply for return context",
        )

    def test_add_comment_preserves_comment_page_and_filter(self):
        self.client.force_login(self.viewer)
        target = (
            reverse("video_detail", kwargs={"pk": self.video.pk})
            + "?comments=questions&comments_page=2#comments-heading"
        )

        response = self.client.post(
            reverse("add_comment", kwargs={"pk": self.video.pk}),
            {"comment": "New top-level comment", "next": target},
        )

        self.assertRedirects(response, target, fetch_redirect_response=False)
        self.assertTrue(
            Comment.objects.filter(
                video=self.video,
                parent__isnull=True,
                comment="New top-level comment",
            ).exists()
        )

    def test_add_reply_preserves_full_thread_route(self):
        self.client.force_login(self.viewer)
        target = reverse("comment_thread", kwargs={"pk": self.parent.pk})

        response = self.client.post(
            reverse("add_comment_reply", kwargs={"pk": self.parent.pk}),
            {"comment": "New thread reply", "next": target},
        )

        self.assertRedirects(response, target, fetch_redirect_response=False)
        self.assertTrue(
            Comment.objects.filter(
                parent=self.parent,
                author=self.viewer,
                comment="New thread reply",
            ).exists()
        )

    def test_external_return_target_is_rejected(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("add_comment_reply", kwargs={"pk": self.parent.pk}),
            {
                "comment": "Safe fallback reply",
                "next": "https://evil.example/phish",
            },
        )

        self.assertRedirects(
            response,
            reverse("video_detail", kwargs={"pk": self.video.pk}),
            fetch_redirect_response=False,
        )

    def test_comment_edit_preserves_origin_through_get_and_post(self):
        self.client.force_login(self.viewer)
        target = reverse("comment_thread", kwargs={"pk": self.parent.pk})
        edit_url = (
            reverse("comment_edit", kwargs={"pk": self.reply.pk})
            + f"?next={quote(target, safe='')}"
        )

        get_response = self.client.get(edit_url)
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(
            get_response,
            f'name="next" value="{target}"',
            html=False,
        )
        self.assertContains(
            get_response,
            f'href="{target}"',
            html=False,
        )

        post_response = self.client.post(
            reverse("comment_edit", kwargs={"pk": self.reply.pk}),
            {"comment": "Edited in thread", "next": target},
        )
        self.assertRedirects(
            post_response,
            target,
            fetch_redirect_response=False,
        )
        self.reply.refresh_from_db()
        self.assertEqual(self.reply.comment, "Edited in thread")

    def test_comment_delete_preserves_origin_through_get_and_post(self):
        self.client.force_login(self.viewer)
        target = (
            reverse("video_detail", kwargs={"pk": self.video.pk})
            + "?comments_page=2#comments-heading"
        )
        delete_url = (
            reverse("comment_delete", kwargs={"pk": self.reply.pk})
            + f"?next={quote(target, safe='')}"
        )

        get_response = self.client.get(delete_url)
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(
            get_response,
            f'name="next" value="{target}"',
            html=False,
        )
        self.assertContains(
            get_response,
            f'href="{target}"',
            html=False,
        )

        post_response = self.client.post(
            reverse("comment_delete", kwargs={"pk": self.reply.pk}),
            {"next": target},
        )
        self.assertRedirects(
            post_response,
            target,
            fetch_redirect_response=False,
        )
        self.assertFalse(Comment.objects.filter(pk=self.reply.pk).exists())

    def test_templates_include_current_return_context(self):
        self.client.force_login(self.viewer)
        detail = reverse("video_detail", kwargs={"pk": self.video.pk})
        response = self.client.get(detail, {"comments_page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="next"', html=False)
        self.assertContains(
            response,
            quote(f"{detail}?comments_page=2", safe=""),
            html=False,
        )
