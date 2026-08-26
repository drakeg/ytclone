from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import Channel, Notification, Video
from .services.notifications import (
    deliver_due_scheduled_upload_notifications,
    notify_new_upload,
)


class ScheduledUploadNotificationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="scheduler", password="password123")
        self.subscriber = User.objects.create_user(username="subscriber", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Scheduled Channel", description="")
        self.channel.subscribers.add(self.subscriber, self.creator)

    def make_video(self, *, status=Video.PublicationStatus.SCHEDULED, publish_at=None, deleted_at=None):
        return Video.objects.create(
            title="Scheduled upload",
            description="",
            thumbnail="videos/thumbnails/scheduled.jpg",
            video_file="videos/files/scheduled.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=status,
            publish_at=publish_at,
            deleted_at=deleted_at,
        )

    def upload_notifications(self, video):
        return Notification.objects.filter(video=video, kind=Notification.Kind.UPLOAD)

    def test_future_scheduled_video_does_not_notify(self):
        video = self.make_video(publish_at=timezone.now() + timedelta(hours=1))
        videos, notifications = deliver_due_scheduled_upload_notifications()
        self.assertEqual((videos, notifications), (0, 0))
        self.assertFalse(self.upload_notifications(video).exists())
        video.refresh_from_db()
        self.assertIsNone(video.upload_notifications_sent_at)

    def test_due_scheduled_video_notifies_subscribers_once(self):
        video = self.make_video(publish_at=timezone.now() - timedelta(seconds=1))
        first = deliver_due_scheduled_upload_notifications()
        second = deliver_due_scheduled_upload_notifications()
        self.assertEqual(first, (1, 1))
        self.assertEqual(second, (0, 0))
        notification = self.upload_notifications(video).get()
        self.assertEqual(notification.recipient, self.subscriber)
        self.assertNotEqual(notification.recipient, self.creator)
        video.refresh_from_db()
        self.assertIsNotNone(video.upload_notifications_sent_at)

    def test_draft_unlisted_and_trashed_videos_are_ignored(self):
        now = timezone.now() - timedelta(minutes=1)
        draft = self.make_video(status=Video.PublicationStatus.DRAFT, publish_at=now)
        unlisted = self.make_video(status=Video.PublicationStatus.UNLISTED, publish_at=now)
        trashed = self.make_video(publish_at=now, deleted_at=timezone.now())
        self.assertEqual(deliver_due_scheduled_upload_notifications(), (0, 0))
        for video in (draft, unlisted, trashed):
            video.refresh_from_db()
            self.assertIsNone(video.upload_notifications_sent_at)
            self.assertFalse(self.upload_notifications(video).exists())

    def test_immediate_upload_notification_is_idempotent(self):
        video = self.make_video(status=Video.PublicationStatus.PUBLISHED, publish_at=None)
        self.assertEqual(notify_new_upload(video), 1)
        self.assertEqual(notify_new_upload(video), 0)
        self.assertEqual(self.upload_notifications(video).count(), 1)

    def test_management_command_delivers_due_notifications(self):
        video = self.make_video(publish_at=timezone.now() - timedelta(seconds=1))
        output = StringIO()
        call_command("deliver_scheduled_upload_notifications", stdout=output)
        self.assertIn("Processed 1 due scheduled video(s)", output.getvalue())
        self.assertEqual(self.upload_notifications(video).count(), 1)

    def test_normal_template_request_delivers_due_notifications(self):
        video = self.make_video(publish_at=timezone.now() - timedelta(seconds=1))
        response = self.client.get("/videos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.upload_notifications(video).count(), 1)
