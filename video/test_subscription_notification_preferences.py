from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Channel, Notification, SubscriptionNotificationPreference, Video
from .services.notifications import deliver_due_scheduled_upload_notifications, notify_new_upload


class SubscriptionNotificationPreferenceTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="pw")
        self.subscriber = User.objects.create_user(username="subscriber", password="pw")
        self.other_subscriber = User.objects.create_user(username="other", password="pw")
        self.channel = Channel.objects.create(name="Channel", description="", owner=self.creator)
        self.channel.subscribers.add(self.subscriber, self.other_subscriber)

    def video(self, title="Upload", **overrides):
        values = {
            "title": title,
            "description": title,
            "thumbnail": "videos/thumb.jpg",
            "video_file": "videos/video.mp4",
            "author": self.creator,
            "channel": self.channel,
            "publication_status": Video.PublicationStatus.PUBLISHED,
        }
        values.update(overrides)
        return Video.objects.create(**values)

    def test_missing_preference_defaults_to_enabled(self):
        video = self.video()
        self.assertEqual(notify_new_upload(video), 2)
        self.assertSetEqual(
            set(Notification.objects.filter(kind=Notification.Kind.UPLOAD).values_list("recipient__username", flat=True)),
            {"subscriber", "other"},
        )

    def test_disabled_preference_suppresses_immediate_upload_notification(self):
        SubscriptionNotificationPreference.objects.create(
            user=self.subscriber,
            channel=self.channel,
            upload_notifications_enabled=False,
        )
        video = self.video()
        self.assertEqual(notify_new_upload(video), 1)
        self.assertFalse(Notification.objects.filter(recipient=self.subscriber, kind=Notification.Kind.UPLOAD).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.other_subscriber, kind=Notification.Kind.UPLOAD).exists())

    def test_disabled_preference_suppresses_scheduled_upload_notification(self):
        SubscriptionNotificationPreference.objects.create(
            user=self.subscriber,
            channel=self.channel,
            upload_notifications_enabled=False,
        )
        due = timezone.now() - timedelta(minutes=1)
        self.video(
            title="Scheduled",
            publication_status=Video.PublicationStatus.SCHEDULED,
            publish_at=due,
        )
        self.assertEqual(deliver_due_scheduled_upload_notifications(now=timezone.now()), (1, 1))
        self.assertFalse(Notification.objects.filter(recipient=self.subscriber, kind=Notification.Kind.UPLOAD).exists())
        self.assertTrue(Notification.objects.filter(recipient=self.other_subscriber, kind=Notification.Kind.UPLOAD).exists())

    def test_subscriber_can_toggle_upload_notifications_without_unsubscribing(self):
        self.client.force_login(self.subscriber)
        url = reverse("subscription_upload_notifications", kwargs={"pk": self.channel.pk})
        response = self.client.post(url, {"enabled": "0"})
        self.assertRedirects(response, reverse("channel_detail", kwargs={"pk": self.channel.pk}))
        self.assertTrue(self.channel.subscribers.filter(pk=self.subscriber.pk).exists())
        preference = SubscriptionNotificationPreference.objects.get(user=self.subscriber, channel=self.channel)
        self.assertFalse(preference.upload_notifications_enabled)

        self.client.post(url, {"enabled": "1"})
        preference.refresh_from_db()
        self.assertTrue(preference.upload_notifications_enabled)

    def test_non_subscriber_cannot_set_preference(self):
        outsider = User.objects.create_user(username="outsider", password="pw")
        self.client.force_login(outsider)
        response = self.client.post(
            reverse("subscription_upload_notifications", kwargs={"pk": self.channel.pk}),
            {"enabled": "0"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(SubscriptionNotificationPreference.objects.filter(user=outsider, channel=self.channel).exists())

    def test_unsubscribe_removes_preference(self):
        SubscriptionNotificationPreference.objects.create(
            user=self.subscriber,
            channel=self.channel,
            upload_notifications_enabled=False,
        )
        self.client.force_login(self.subscriber)
        self.client.post(reverse("subscribe", kwargs={"pk": self.channel.pk}))
        self.assertFalse(self.channel.subscribers.filter(pk=self.subscriber.pk).exists())
        self.assertFalse(SubscriptionNotificationPreference.objects.filter(user=self.subscriber, channel=self.channel).exists())

    def test_channel_page_shows_current_notification_state_for_subscriber(self):
        SubscriptionNotificationPreference.objects.create(
            user=self.subscriber,
            channel=self.channel,
            upload_notifications_enabled=False,
        )
        self.client.force_login(self.subscriber)
        response = self.client.get(reverse("channel_detail", kwargs={"pk": self.channel.pk}))
        self.assertContains(response, "Upload notifications: Off")
        self.assertContains(response, reverse("subscription_upload_notifications", kwargs={"pk": self.channel.pk}))
