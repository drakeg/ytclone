from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse

from .community_models import CommunityPost, CommunityReply
from .models import Channel, Video
from .moderation_models import (
    CommunityPostModerationState,
    CommunityReplyModerationState,
    ModerationAuditEvent,
    VideoModerationState,
)
from .services.publication import bulk_update_publication


class ModerationSanctionTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff", password="password123", is_staff=True)
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.editor = User.objects.create_user(username="editor", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Channel", description="")
        self.channel.memberships.create(user=self.editor)
        self.video = Video.objects.create(
            title="Public video",
            description="",
            thumbnail="videos/thumbnails/a.jpg",
            video_file="videos/files/a.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        self.post = CommunityPost.objects.create(
            channel=self.channel,
            author=self.creator,
            body="Hidden policy-violating community post body",
        )
        self.reply = CommunityReply.objects.create(
            post=self.post,
            author=self.viewer,
            body="Hidden abusive reply body",
        )

    def test_staff_video_takedown_requires_reason_and_restores_original_state(self):
        self.client.force_login(self.staff)
        url = reverse("site_admin_video_moderate", args=[self.video.pk])
        response = self.client.post(url, {"action": "hide", "reason": ""})
        self.assertEqual(response.status_code, 400)
        self.client.post(url, {"action": "hide", "reason": "Policy violation"})
        self.video.refresh_from_db()
        self.assertEqual(self.video.publication_status, Video.PublicationStatus.DRAFT)
        self.assertTrue(VideoModerationState.objects.filter(video=self.video).exists())
        self.assertFalse(Video.objects.visible_to(AnonymousUser()).filter(pk=self.video.pk).exists())
        self.assertTrue(ModerationAuditEvent.objects.filter(action="video_takedown", target_id=self.video.pk).exists())
        self.client.post(url, {"action": "restore", "reason": "Appeal accepted"})
        self.video.refresh_from_db()
        self.assertEqual(self.video.publication_status, Video.PublicationStatus.PUBLISHED)
        self.assertFalse(VideoModerationState.objects.filter(video=self.video).exists())
        self.assertTrue(Video.objects.visible_to(AnonymousUser()).filter(pk=self.video.pk).exists())

    def test_creator_cannot_republish_active_staff_takedown(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse("site_admin_video_moderate", args=[self.video.pk]),
            {"action": "hide", "reason": "Policy violation"},
        )
        self.video.publication_status = Video.PublicationStatus.PUBLISHED
        self.video.save()
        self.video.refresh_from_db()
        self.assertEqual(self.video.publication_status, Video.PublicationStatus.DRAFT)

        updated = bulk_update_publication(
            self.creator,
            [self.video.pk],
            Video.PublicationStatus.PUBLISHED,
        )
        self.assertEqual(updated, 0)
        self.video.refresh_from_db()
        self.assertEqual(self.video.publication_status, Video.PublicationStatus.DRAFT)

    def test_non_staff_cannot_use_site_sanctions(self):
        self.client.force_login(self.creator)
        response = self.client.post(
            reverse("site_admin_video_moderate", args=[self.video.pk]),
            {"action": "hide", "reason": "No"},
        )
        self.assertEqual(response.status_code, 302)
        self.video.refresh_from_db()
        self.assertEqual(self.video.publication_status, Video.PublicationStatus.PUBLISHED)

    def test_staff_can_suspend_and_reactivate_user_with_audit(self):
        self.client.force_login(self.staff)
        url = reverse("site_admin_user_moderate", args=[self.viewer.pk])
        self.client.post(url, {"action": "suspend", "reason": "Abuse"})
        self.viewer.refresh_from_db()
        self.assertFalse(self.viewer.is_active)
        self.assertTrue(ModerationAuditEvent.objects.filter(action="user_suspend", target_id=self.viewer.pk).exists())
        self.client.post(url, {"action": "reactivate", "reason": "Resolved"})
        self.viewer.refresh_from_db()
        self.assertTrue(self.viewer.is_active)

    def test_staff_cannot_suspend_self(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("site_admin_user_moderate", args=[self.staff.pk]),
            {"action": "suspend", "reason": "Mistake"},
        )
        self.assertEqual(response.status_code, 400)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)

    def test_staff_comment_moderation_requires_reason_and_is_audited(self):
        from .models import Comment

        comment = Comment.objects.create(video=self.video, author=self.viewer, comment="Moderate")
        self.client.force_login(self.staff)
        url = reverse("site_admin_comment_moderate", args=[comment.pk])
        self.assertEqual(self.client.post(url, {"action": "hide"}).status_code, 400)
        self.client.post(url, {"action": "hide", "reason": "Harassment"})
        comment.refresh_from_db()
        self.assertTrue(comment.is_hidden)
        self.assertTrue(ModerationAuditEvent.objects.filter(action="comment_hide", target_id=comment.pk).exists())

    def test_staff_can_hide_and_restore_community_content(self):
        self.client.force_login(self.staff)
        post_url = reverse("site_admin_community_post_moderate", args=[self.post.pk])
        reply_url = reverse("site_admin_community_reply_moderate", args=[self.reply.pk])
        self.client.post(post_url, {"action": "hide", "reason": "Spam"})
        self.client.post(reply_url, {"action": "hide", "reason": "Harassment"})
        self.assertTrue(CommunityPostModerationState.objects.filter(post=self.post).exists())
        self.assertTrue(CommunityReplyModerationState.objects.filter(reply=self.reply).exists())
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertNotContains(response, "Hidden policy-violating community post body")
        self.client.force_login(self.staff)
        self.client.post(post_url, {"action": "restore", "reason": "Reviewed"})
        self.client.post(reply_url, {"action": "restore", "reason": "Reviewed"})
        self.assertFalse(CommunityPostModerationState.objects.filter(post=self.post).exists())
        self.assertFalse(CommunityReplyModerationState.objects.filter(reply=self.reply).exists())

    def test_channel_editor_can_moderate_reply_but_other_user_cannot(self):
        url = reverse("community_reply_moderate", args=[self.reply.pk])
        self.client.force_login(self.editor)
        self.client.post(url, {"action": "hide"})
        self.assertTrue(CommunityReplyModerationState.objects.filter(reply=self.reply).exists())
        self.client.force_login(self.viewer)
        page = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertNotContains(page, "Hidden abusive reply body")
        response = self.client.post(url, {"action": "restore"})
        self.assertEqual(response.status_code, 404)
        self.assertTrue(CommunityReplyModerationState.objects.filter(reply=self.reply).exists())
