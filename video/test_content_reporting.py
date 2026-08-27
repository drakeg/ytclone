from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .community_models import CommunityPost, CommunityReply
from .models import Channel, Comment, Video
from .reporting_models import ContentReport


class ContentReportingTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff", password="password123", is_staff=True
        )
        self.creator = User.objects.create_user(
            username="creator", password="password123"
        )
        self.viewer = User.objects.create_user(
            username="viewer", password="password123"
        )
        self.other = User.objects.create_user(
            username="other", password="password123"
        )
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Reportable Channel",
            description="A reportable channel",
        )
        self.video = Video.objects.create(
            title="Reportable Video",
            description="Video body",
            thumbnail="videos/thumbnails/a.jpg",
            video_file="videos/files/a.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        self.comment = Comment.objects.create(
            video=self.video,
            author=self.creator,
            comment="Reportable comment body",
        )
        self.reply = Comment.objects.create(
            video=self.video,
            author=self.other,
            parent=self.comment,
            comment="Reportable reply body",
        )
        self.post = CommunityPost.objects.create(
            channel=self.channel,
            author=self.creator,
            body="Reportable community post body",
        )
        self.community_reply = CommunityReply.objects.create(
            post=self.post,
            author=self.other,
            body="Reportable community reply body",
        )

    def report_url(self, target_type, target_id):
        return reverse("report_content", args=[target_type, target_id])

    def test_reporting_requires_login(self):
        response = self.client.get(self.report_url("video", self.video.pk))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_visible_targets_can_be_reported_and_duplicate_open_report_is_suppressed(self):
        self.client.force_login(self.viewer)
        url = self.report_url("video", self.video.pk)
        response = self.client.post(
            url,
            {"reason": ContentReport.Reason.SPAM, "details": "Misleading metadata"},
        )
        self.assertRedirects(response, reverse("video_detail", args=[self.video.pk]))
        report = ContentReport.objects.get()
        self.assertEqual(report.reporter, self.viewer)
        self.assertEqual(report.target_type, ContentReport.TargetType.VIDEO)
        self.assertEqual(report.target_id, self.video.pk)
        self.assertEqual(report.details, "Misleading metadata")

        self.client.post(
            url,
            {"reason": ContentReport.Reason.HARASSMENT, "details": "Second attempt"},
        )
        self.assertEqual(ContentReport.objects.count(), 1)

    def test_users_cannot_report_own_or_inaccessible_content(self):
        self.client.force_login(self.creator)
        self.assertEqual(
            self.client.get(self.report_url("video", self.video.pk)).status_code,
            400,
        )
        draft = Video.objects.create(
            title="Private draft",
            description="",
            thumbnail="videos/thumbnails/b.jpg",
            video_file="videos/files/b.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        self.client.force_login(self.viewer)
        self.assertEqual(
            self.client.get(self.report_url("video", draft.pk)).status_code,
            404,
        )

    def test_all_supported_target_types_resolve_for_visible_content(self):
        self.client.force_login(self.viewer)
        targets = (
            ("channel", self.channel.pk),
            ("video", self.video.pk),
            ("comment", self.comment.pk),
            ("comment", self.reply.pk),
            ("community_post", self.post.pk),
            ("community_reply", self.community_reply.pk),
        )
        for target_type, target_id in targets:
            with self.subTest(target_type=target_type, target_id=target_id):
                response = self.client.get(self.report_url(target_type, target_id))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Private moderation report")

    def test_report_actions_render_on_viewer_surfaces_but_not_own_content(self):
        self.client.force_login(self.viewer)
        video_page = self.client.get(reverse("video_detail", args=[self.video.pk]))
        self.assertContains(video_page, self.report_url("video", self.video.pk))
        self.assertContains(video_page, self.report_url("comment", self.comment.pk))
        self.assertContains(video_page, self.report_url("comment", self.reply.pk))
        channel_page = self.client.get(reverse("channel_detail", args=[self.channel.pk]))
        self.assertContains(channel_page, self.report_url("channel", self.channel.pk))
        community_page = self.client.get(reverse("channel_community", args=[self.channel.pk]))
        self.assertContains(community_page, self.report_url("community_post", self.post.pk))
        self.assertContains(
            community_page,
            self.report_url("community_reply", self.community_reply.pk),
        )

        self.client.force_login(self.creator)
        own_channel_page = self.client.get(reverse("channel_detail", args=[self.channel.pk]))
        self.assertNotContains(own_channel_page, self.report_url("channel", self.channel.pk))
        own_video_page = self.client.get(reverse("video_detail", args=[self.video.pk]))
        self.assertNotContains(own_video_page, self.report_url("video", self.video.pk))

    def test_staff_queue_is_private_and_review_records_resolution(self):
        ContentReport.objects.create(
            reporter=self.viewer,
            target_type=ContentReport.TargetType.VIDEO,
            target_id=self.video.pk,
            target_label=self.video.title,
            reason=ContentReport.Reason.OTHER,
            details="Please review",
        )
        self.client.force_login(self.creator)
        self.assertEqual(
            self.client.get(reverse("site_admin_report_queue")).status_code,
            302,
        )

        self.client.force_login(self.staff)
        queue = self.client.get(reverse("site_admin_report_queue"))
        self.assertEqual(queue.status_code, 200)
        self.assertContains(queue, "@viewer")
        self.assertContains(queue, "Please review")
        report = ContentReport.objects.get()
        bad = self.client.post(
            reverse("site_admin_report_review", args=[report.pk]),
            {"action": "resolve", "resolution_note": ""},
        )
        self.assertEqual(bad.status_code, 400)
        self.client.post(
            reverse("site_admin_report_review", args=[report.pk]),
            {"action": "resolve", "resolution_note": "Reviewed and handled"},
        )
        report.refresh_from_db()
        self.assertEqual(report.status, ContentReport.Status.RESOLVED)
        self.assertEqual(report.reviewed_by, self.staff)
        self.assertIsNotNone(report.reviewed_at)
        self.assertEqual(report.resolution_note, "Reviewed and handled")

    def test_resolving_report_allows_future_report_without_deleting_history(self):
        self.client.force_login(self.viewer)
        url = self.report_url("video", self.video.pk)
        self.client.post(url, {"reason": ContentReport.Reason.SPAM})
        first = ContentReport.objects.get()
        first.status = ContentReport.Status.DISMISSED
        first.save(update_fields=["status"])
        self.client.post(url, {"reason": ContentReport.Reason.OTHER})
        self.assertEqual(ContentReport.objects.count(), 2)
        self.assertEqual(ContentReport.objects.filter(status=ContentReport.Status.OPEN).count(), 1)
