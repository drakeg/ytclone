from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Comment, Video


class CommentModerationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator", password="password123"
        )
        self.other_creator = User.objects.create_user(
            username="other-creator", password="password123"
        )
        self.commenter = User.objects.create_user(
            username="commenter", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General",
            thumbnail="categories/general.jpg",
        )
        self.video = self.create_video("Creator video", self.creator)
        self.foreign_video = self.create_video("Foreign video", self.other_creator)
        self.trashed_video = self.create_video("Trashed video", self.creator)
        self.trashed_video.deleted_at = timezone.now()
        self.trashed_video.save(update_fields=["deleted_at"])
        self.visible = Comment.objects.create(
            video=self.video,
            author=self.commenter,
            comment="Visible comment",
        )
        self.hidden = Comment.objects.create(
            video=self.video,
            author=self.commenter,
            comment="Hidden comment",
            is_hidden=True,
        )
        self.foreign = Comment.objects.create(
            video=self.foreign_video,
            author=self.commenter,
            comment="Foreign comment",
        )
        self.trashed = Comment.objects.create(
            video=self.trashed_video,
            author=self.commenter,
            comment="Trashed comment",
        )
        Comment.objects.filter(pk=self.visible.pk).update(
            pub_date=timezone.now() - timedelta(hours=1)
        )

    def create_video(self, title, author):
        return Video.objects.create(
            title=title,
            description=title,
            thumbnail=f"videos/{title}.jpg",
            video_file=f"videos/{title}.mp4",
            author=author,
            category=self.category,
        )

    def test_moderation_requires_login(self):
        response = self.client.get(reverse("creator_comment_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_queue_is_owner_scoped_and_excludes_trashed_videos(self):
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("creator_comment_list"))
        self.assertContains(response, self.visible.comment)
        self.assertContains(response, self.hidden.comment)
        self.assertNotContains(response, self.foreign.comment)
        self.assertNotContains(response, self.trashed.comment)

    def test_filters_visible_and_hidden_comments(self):
        self.client.login(username="creator", password="password123")
        for status, expected in (("visible", self.visible), ("hidden", self.hidden)):
            with self.subTest(status=status):
                response = self.client.get(
                    reverse("creator_comment_list"), {"status": status}
                )
                self.assertEqual(list(response.context["comments"]), [expected])
                self.assertEqual(response.context["selected_filter"], status)

    def test_comments_are_ordered_newest_first(self):
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("creator_comment_list"))
        self.assertEqual(
            list(response.context["comments"]), [self.hidden, self.visible]
        )

    def test_invalid_filter_falls_back_to_all(self):
        self.client.login(username="creator", password="password123")
        response = self.client.get(
            reverse("creator_comment_list"), {"status": "deleted"}
        )
        self.assertEqual(response.context["selected_filter"], "all")
        self.assertEqual(len(response.context["comments"]), 2)

    def test_bulk_moderation_requires_post(self):
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("creator_comment_bulk_moderation"))
        self.assertEqual(response.status_code, 405)

    def test_bulk_hide_and_restore_are_reversible(self):
        self.client.login(username="creator", password="password123")
        url = reverse("creator_comment_bulk_moderation")
        hide_response = self.client.post(
            url, {"comment_ids": [self.visible.pk], "action": "hide"}
        )
        self.assertRedirects(hide_response, reverse("creator_comment_list"))
        self.visible.refresh_from_db()
        self.assertTrue(self.visible.is_hidden)
        restore_response = self.client.post(
            url, {"comment_ids": [self.visible.pk], "action": "restore"}
        )
        self.assertRedirects(restore_response, reverse("creator_comment_list"))
        self.visible.refresh_from_db()
        self.assertFalse(self.visible.is_hidden)

    def test_forged_foreign_and_trashed_comment_ids_are_not_changed(self):
        self.client.login(username="creator", password="password123")
        self.client.post(
            reverse("creator_comment_bulk_moderation"),
            {
                "comment_ids": [self.visible.pk, self.foreign.pk, self.trashed.pk],
                "action": "hide",
            },
        )
        self.visible.refresh_from_db()
        self.foreign.refresh_from_db()
        self.trashed.refresh_from_db()
        self.assertTrue(self.visible.is_hidden)
        self.assertFalse(self.foreign.is_hidden)
        self.assertFalse(self.trashed.is_hidden)

    def test_invalid_action_and_id_do_not_mutate_comments(self):
        self.client.login(username="creator", password="password123")
        url = reverse("creator_comment_bulk_moderation")
        invalid_action = self.client.post(
            url, {"comment_ids": [self.visible.pk], "action": "delete"}
        )
        invalid_id = self.client.post(
            url, {"comment_ids": ["not-an-id"], "action": "hide"}
        )
        self.assertEqual(invalid_action.status_code, 400)
        self.assertEqual(invalid_id.status_code, 400)
        self.visible.refresh_from_db()
        self.assertFalse(self.visible.is_hidden)

    def test_empty_selection_is_safe(self):
        self.client.login(username="creator", password="password123")
        response = self.client.post(
            reverse("creator_comment_bulk_moderation"), {"action": "hide"}
        )
        self.assertRedirects(response, reverse("creator_comment_list"))
        self.visible.refresh_from_db()
        self.assertFalse(self.visible.is_hidden)

    def test_hidden_comments_are_not_rendered_on_video_detail(self):
        response = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk})
        )
        self.assertContains(response, self.visible.comment)
        self.assertNotContains(response, self.hidden.comment)

    def test_empty_state_and_authenticated_navigation(self):
        Comment.objects.filter(video=self.video).delete()
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("creator_comment_list"))
        self.assertContains(response, "No comments match this moderation status.")
        home = self.client.get(reverse("video_list"))
        self.assertContains(home, reverse("creator_comment_list"))

    def test_new_comments_are_visible_by_default(self):
        comment = Comment.objects.create(
            video=self.video,
            author=self.commenter,
            comment="Default visible",
        )
        self.assertFalse(comment.is_hidden)
