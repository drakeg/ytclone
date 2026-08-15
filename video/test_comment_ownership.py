from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Comment, Video


class CommentOwnershipTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator", password="password123"
        )
        self.author = User.objects.create_user(
            username="author", password="password123"
        )
        self.other = User.objects.create_user(
            username="other", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General",
            thumbnail="categories/general.jpg",
        )
        self.video = Video.objects.create(
            title="Public video",
            description="Public",
            thumbnail="videos/public.jpg",
            video_file="videos/public.mp4",
            author=self.creator,
            category=self.category,
        )
        self.comment = Comment.objects.create(
            video=self.video,
            author=self.author,
            comment="Original comment",
        )

    def test_edit_and_delete_require_login(self):
        for name in ("comment_edit", "comment_delete"):
            with self.subTest(name=name):
                response = self.client.get(
                    reverse(name, kwargs={"pk": self.comment.pk})
                )
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/", response.url)

    def test_non_author_and_video_creator_receive_404(self):
        for username in ("other", "creator"):
            self.client.login(username=username, password="password123")
            for name in ("comment_edit", "comment_delete"):
                with self.subTest(username=username, name=name):
                    self.assertEqual(
                        self.client.get(
                            reverse(name, kwargs={"pk": self.comment.pk})
                        ).status_code,
                        404,
                    )
            self.client.logout()

    def test_author_can_edit_comment_text(self):
        self.client.login(username="author", password="password123")
        response = self.client.post(
            reverse("comment_edit", kwargs={"pk": self.comment.pk}),
            {"comment": "Corrected comment"},
        )
        self.assertRedirects(
            response, reverse("video_detail", kwargs={"pk": self.video.pk})
        )
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.comment, "Corrected comment")

    def test_empty_edit_is_rejected(self):
        self.client.login(username="author", password="password123")
        response = self.client.post(
            reverse("comment_edit", kwargs={"pk": self.comment.pk}),
            {"comment": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("comment", response.context["form"].errors)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.comment, "Original comment")

    def test_edit_preserves_hidden_moderation_state(self):
        self.comment.is_hidden = True
        self.comment.save(update_fields=["is_hidden"])
        self.client.login(username="author", password="password123")
        response = self.client.post(
            reverse("comment_edit", kwargs={"pk": self.comment.pk}),
            {"comment": "Edited while hidden"},
        )
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.comment, "Edited while hidden")
        self.assertTrue(self.comment.is_hidden)

    def test_delete_confirmation_does_not_mutate(self):
        self.client.login(username="author", password="password123")
        response = self.client.get(
            reverse("comment_delete", kwargs={"pk": self.comment.pk})
        )
        self.assertContains(response, "This action cannot be undone")
        self.assertTrue(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_author_can_delete_comment_with_post(self):
        self.client.login(username="author", password="password123")
        response = self.client.post(
            reverse("comment_delete", kwargs={"pk": self.comment.pk})
        )
        self.assertRedirects(
            response, reverse("video_detail", kwargs={"pk": self.video.pk})
        )
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())

    def test_inaccessible_draft_comment_cannot_be_edited_or_deleted(self):
        self.video.publication_status = Video.PublicationStatus.DRAFT
        self.video.save(update_fields=["publication_status"])
        self.client.login(username="author", password="password123")
        for name in ("comment_edit", "comment_delete"):
            with self.subTest(name=name):
                self.assertEqual(
                    self.client.post(
                        reverse(name, kwargs={"pk": self.comment.pk}),
                        {"comment": "Blocked"},
                    ).status_code,
                    404,
                )

    def test_trashed_video_comment_cannot_be_edited_or_deleted(self):
        self.video.deleted_at = timezone.now()
        self.video.save(update_fields=["deleted_at"])
        self.client.login(username="author", password="password123")
        for name in ("comment_edit", "comment_delete"):
            with self.subTest(name=name):
                self.assertEqual(
                    self.client.get(
                        reverse(name, kwargs={"pk": self.comment.pk})
                    ).status_code,
                    404,
                )

    def test_controls_render_only_for_comment_author(self):
        detail = reverse("video_detail", kwargs={"pk": self.video.pk})
        edit_url = reverse("comment_edit", kwargs={"pk": self.comment.pk})
        delete_url = reverse("comment_delete", kwargs={"pk": self.comment.pk})
        self.client.login(username="author", password="password123")
        author_response = self.client.get(detail)
        self.client.logout()
        self.client.login(username="other", password="password123")
        other_response = self.client.get(detail)
        self.assertContains(author_response, edit_url)
        self.assertContains(author_response, delete_url)
        self.assertNotContains(other_response, edit_url)
        self.assertNotContains(other_response, delete_url)

    def test_author_edit_does_not_break_creator_moderation(self):
        self.client.login(username="author", password="password123")
        self.client.post(
            reverse("comment_edit", kwargs={"pk": self.comment.pk}),
            {"comment": "Still moderate me"},
        )
        self.client.logout()
        self.client.login(username="creator", password="password123")
        response = self.client.post(
            reverse("creator_comment_bulk_moderation"),
            {"comment_ids": [self.comment.pk], "action": "hide"},
        )
        self.assertRedirects(response, reverse("creator_comment_list"))
        self.comment.refresh_from_db()
        self.assertTrue(self.comment.is_hidden)
