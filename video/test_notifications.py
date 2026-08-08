from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel, Notification, Video


class NotificationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.actor = User.objects.create_user(username="actor", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        category = Category.objects.create(name="General", description="General", thumbnail="categories/general.jpg")
        self.video = Video.objects.create(title="Video", description="Video", thumbnail="videos/video.jpg", video_file="videos/video.mp4", author=self.creator, category=category)
        self.channel = Channel.objects.create(name="Channel", description="Channel", thumbnail="channels/channel.jpg", owner=self.creator)

    def login_actor(self):
        self.client.login(username="actor", password="password123")

    def test_comment_like_dislike_and_subscription_create_notifications(self):
        self.login_actor()
        self.client.post(reverse("add_comment", kwargs={"pk": self.video.pk}), {"comment": "Nice"})
        self.client.post(reverse("like_video", kwargs={"pk": self.video.pk}))
        self.client.post(reverse("dislike_video", kwargs={"pk": self.video.pk}))
        self.client.post(reverse("subscribe", kwargs={"pk": self.channel.pk}))

        self.assertEqual(
            set(Notification.objects.values_list("kind", flat=True)),
            {"comment", "like", "dislike", "subscription"},
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.creator, actor=self.actor
            ).count(),
            4,
        )

    def test_removing_reaction_and_subscription_creates_no_notification(self):
        self.video.likes.add(self.actor)
        self.channel.subscribers.add(self.actor)
        self.login_actor()
        self.client.post(reverse("like_video", kwargs={"pk": self.video.pk}))
        self.client.post(reverse("subscribe", kwargs={"pk": self.channel.pk}))

        self.assertFalse(Notification.objects.exists())

    def test_self_activity_creates_no_notification(self):
        self.client.login(username="creator", password="password123")
        self.client.post(reverse("add_comment", kwargs={"pk": self.video.pk}), {"comment": "Mine"})
        self.client.post(reverse("like_video", kwargs={"pk": self.video.pk}))
        self.client.post(reverse("subscribe", kwargs={"pk": self.channel.pk}))

        self.assertFalse(Notification.objects.exists())

    def test_inbox_requires_login_and_shows_only_current_users_notifications(self):
        own = Notification.objects.create(recipient=self.creator, actor=self.actor, kind=Notification.Kind.LIKE, video=self.video)
        Notification.objects.create(recipient=self.other, actor=self.actor, kind=Notification.Kind.LIKE, video=self.video)
        anonymous = self.client.get(reverse("notification_list"))
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("notification_list"))

        self.assertEqual(anonymous.status_code, 302)
        self.assertEqual(list(response.context["notifications"]), [own])

    def test_unread_count_is_scoped_and_rendered(self):
        Notification.objects.create(recipient=self.creator, actor=self.actor, kind=Notification.Kind.LIKE, video=self.video)
        Notification.objects.create(recipient=self.other, actor=self.actor, kind=Notification.Kind.LIKE, video=self.video)
        self.client.login(username="creator", password="password123")

        response = self.client.get(reverse("video_list"))

        self.assertEqual(response.context["unread_notification_count"], 1)
        self.assertContains(response, "Notifications")

    def test_user_can_mark_own_notification_read(self):
        notification = Notification.objects.create(recipient=self.creator, actor=self.actor, kind=Notification.Kind.LIKE, video=self.video)
        self.client.login(username="creator", password="password123")

        response = self.client.post(reverse("notification_mark_read", kwargs={"pk": notification.pk}))

        self.assertRedirects(response, reverse("notification_list"))
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_user_cannot_mark_another_users_notification_read(self):
        notification = Notification.objects.create(recipient=self.other, actor=self.actor, kind=Notification.Kind.LIKE, video=self.video)
        self.client.login(username="creator", password="password123")

        response = self.client.post(reverse("notification_mark_read", kwargs={"pk": notification.pk}))

        self.assertEqual(response.status_code, 404)
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)

    def test_mark_all_read_changes_only_current_users_notifications(self):
        own = Notification.objects.create(recipient=self.creator, actor=self.actor, kind=Notification.Kind.LIKE, video=self.video)
        other = Notification.objects.create(recipient=self.other, actor=self.actor, kind=Notification.Kind.LIKE, video=self.video)
        self.client.login(username="creator", password="password123")

        self.client.post(reverse("notification_mark_all_read"))

        own.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(own.is_read)
        self.assertFalse(other.is_read)

    def test_read_mutations_reject_get(self):
        notification = Notification.objects.create(recipient=self.creator, actor=self.actor, kind=Notification.Kind.LIKE, video=self.video)
        self.client.login(username="creator", password="password123")

        responses = [
            self.client.get(reverse("notification_mark_read", kwargs={"pk": notification.pk})),
            self.client.get(reverse("notification_mark_all_read")),
        ]

        self.assertTrue(all(response.status_code == 405 for response in responses))

    def test_empty_inbox_has_useful_state(self):
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("notification_list"))
        self.assertContains(response, "You have no notifications yet.")
