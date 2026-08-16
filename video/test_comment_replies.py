from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Comment, Notification, Video


class CommentReplyTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator", password="password123"
        )
        self.parent_author = User.objects.create_user(
            username="parent-author", password="password123"
        )
        self.replier = User.objects.create_user(
            username="replier", password="password123"
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
            title="Reply video",
            description="Reply video",
            thumbnail="videos/reply.jpg",
            video_file="videos/reply.mp4",
            author=self.creator,
            category=self.category,
        )
        self.parent = Comment.objects.create(
            video=self.video,
            author=self.parent_author,
            comment="Parent comment",
        )

    def reply_url(self, comment=None):
        return reverse(
            "add_comment_reply", kwargs={"pk": (comment or self.parent).pk}
        )

    def create_reply(self, text="A reply", author=None, parent=None, hidden=False):
        return Comment.objects.create(
            video=self.video,
            author=author or self.replier,
            parent=parent or self.parent,
            comment=text,
            is_hidden=hidden,
        )

    def test_reply_requires_login(self):
        response = self.client.post(self.reply_url(), {"comment": "No login"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
        self.assertEqual(Comment.objects.count(), 1)

    def test_viewer_can_create_same_video_reply(self):
        self.client.login(username="replier", password="password123")
        response = self.client.post(self.reply_url(), {"comment": "New reply"})
        self.assertRedirects(
            response, reverse("video_detail", kwargs={"pk": self.video.pk})
        )
        reply = Comment.objects.get(parent=self.parent)
        self.assertEqual(reply.video, self.video)
        self.assertEqual(reply.author, self.replier)

    def test_reply_to_reply_is_rejected(self):
        reply = self.create_reply()
        self.client.login(username="other", password="password123")
        response = self.client.post(
            self.reply_url(reply), {"comment": "Too deeply nested"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.count(), 2)

    def test_hidden_parent_and_inaccessible_video_reject_replies(self):
        self.client.login(username="replier", password="password123")
        self.parent.is_hidden = True
        self.parent.save(update_fields=["is_hidden"])
        self.assertEqual(
            self.client.post(self.reply_url(), {"comment": "Hidden"}).status_code,
            404,
        )
        self.parent.is_hidden = False
        self.parent.save(update_fields=["is_hidden"])
        for status in (Video.PublicationStatus.DRAFT,):
            self.video.publication_status = status
            self.video.save(update_fields=["publication_status"])
            self.assertEqual(
                self.client.post(self.reply_url(), {"comment": "Private"}).status_code,
                404,
            )
        self.video.publication_status = Video.PublicationStatus.PUBLISHED
        self.video.deleted_at = timezone.now()
        self.video.save(update_fields=["publication_status", "deleted_at"])
        self.assertEqual(
            self.client.post(self.reply_url(), {"comment": "Trashed"}).status_code,
            404,
        )

    def test_empty_reply_is_safe(self):
        self.client.login(username="replier", password="password123")
        response = self.client.post(self.reply_url(), {"comment": ""})
        self.assertRedirects(
            response, reverse("video_detail", kwargs={"pk": self.video.pk})
        )
        self.assertEqual(Comment.objects.count(), 1)

    def test_visible_replies_render_under_parent_in_order(self):
        first = self.create_reply("First reply")
        second = self.create_reply("Second reply", author=self.other)
        response = self.client.get(
            reverse("video_detail", kwargs={"pk": self.video.pk})
        )
        content = response.content.decode()
        self.assertContains(response, self.parent.comment, count=1)
        self.assertContains(response, first.comment, count=1)
        self.assertContains(response, second.comment, count=1)
        self.assertLess(content.index(first.comment), content.index(second.comment))

    def test_parent_and_reply_moderation_have_expected_scope(self):
        visible_reply = self.create_reply("Visible reply")
        hidden_reply = self.create_reply("Hidden reply", hidden=True)
        detail = reverse("video_detail", kwargs={"pk": self.video.pk})
        response = self.client.get(detail)
        self.assertContains(response, visible_reply.comment)
        self.assertNotContains(response, hidden_reply.comment)
        self.parent.is_hidden = True
        self.parent.save(update_fields=["is_hidden"])
        hidden_thread = self.client.get(detail)
        self.assertNotContains(hidden_thread, self.parent.comment)
        self.assertNotContains(hidden_thread, visible_reply.comment)

    def test_reply_reuses_author_edit_and_delete(self):
        reply = self.create_reply()
        self.client.login(username="replier", password="password123")
        edit = self.client.post(
            reverse("comment_edit", kwargs={"pk": reply.pk}),
            {"comment": "Edited reply"},
        )
        self.assertEqual(edit.status_code, 302)
        reply.refresh_from_db()
        self.assertEqual(reply.comment, "Edited reply")
        delete = self.client.post(
            reverse("comment_delete", kwargs={"pk": reply.pk})
        )
        self.assertEqual(delete.status_code, 302)
        self.assertFalse(Comment.objects.filter(pk=reply.pk).exists())

    def test_deleting_parent_cascades_to_replies(self):
        reply = self.create_reply()
        self.client.login(username="parent-author", password="password123")
        confirmation = self.client.get(
            reverse("comment_delete", kwargs={"pk": self.parent.pk})
        )
        self.assertContains(confirmation, "Replies in this thread")
        self.client.post(reverse("comment_delete", kwargs={"pk": self.parent.pk}))
        self.assertFalse(Comment.objects.filter(pk__in=[self.parent.pk, reply.pk]).exists())

    def test_reply_notifies_creator_and_parent_author(self):
        self.client.login(username="replier", password="password123")
        self.client.post(self.reply_url(), {"comment": "Notify both"})
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.creator, kind=Notification.Kind.COMMENT
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.parent_author, kind=Notification.Kind.REPLY
            ).exists()
        )

    def test_creator_parent_receives_only_existing_comment_notification(self):
        creator_parent = Comment.objects.create(
            video=self.video,
            author=self.creator,
            comment="Creator parent",
        )
        self.client.login(username="replier", password="password123")
        self.client.post(
            self.reply_url(creator_parent), {"comment": "No duplicate"}
        )
        notifications = Notification.objects.filter(recipient=self.creator)
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.get().kind, Notification.Kind.COMMENT)

    def test_self_reply_does_not_notify_parent_author(self):
        self.client.login(username="parent-author", password="password123")
        self.client.post(self.reply_url(), {"comment": "Self reply"})
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.parent_author, kind=Notification.Kind.REPLY
            ).exists()
        )

    def test_creator_queue_includes_replies_for_moderation(self):
        reply = self.create_reply("Moderate this reply")
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("creator_comment_list"))
        self.assertContains(response, reply.comment)
        self.assertContains(response, "Reply:")
        self.client.post(
            reverse("creator_comment_bulk_moderation"),
            {"comment_ids": [reply.pk], "action": "hide"},
        )
        reply.refresh_from_db()
        self.assertTrue(reply.is_hidden)
