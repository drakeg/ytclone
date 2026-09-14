from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Notification


class NotificationPaginationTests(TestCase):
    def setUp(self):
        self.recipient = User.objects.create_user(
            username="recipient", password="password123"
        )
        self.actor = User.objects.create_user(
            username="actor-pagination", password="password123"
        )
        self.other = User.objects.create_user(
            username="other-pagination", password="password123"
        )
        self.client.login(username="recipient", password="password123")

    def create_notifications(self, count, *, recipient=None):
        recipient = recipient or self.recipient
        return [
            Notification.objects.create(
                recipient=recipient,
                actor=self.actor,
                kind=Notification.Kind.LIKE,
            )
            for _ in range(count)
        ]

    def test_inbox_is_paginated_at_twenty_four(self):
        notifications = self.create_notifications(25)

        response = self.client.get(reverse("notification_list"))
        page = response.context["notifications"]

        self.assertEqual(page.paginator.count, 25)
        self.assertEqual(page.paginator.num_pages, 2)
        self.assertEqual(len(page.object_list), 24)
        self.assertEqual(page.object_list[0], notifications[-1])
        self.assertContains(response, "Page 1 of 2")
        self.assertContains(response, "?page=2")

    def test_second_page_contains_oldest_remaining_notification(self):
        notifications = self.create_notifications(25)

        response = self.client.get(reverse("notification_list") + "?page=2")
        page = response.context["notifications"]

        self.assertEqual(page.number, 2)
        self.assertEqual(list(page.object_list), [notifications[0]])
        self.assertContains(response, "Page 2 of 2")
        self.assertContains(response, "?page=1")

    def test_invalid_and_out_of_range_pages_fall_back_safely(self):
        self.create_notifications(25)

        malformed = self.client.get(reverse("notification_list") + "?page=nope")
        out_of_range = self.client.get(reverse("notification_list") + "?page=999")

        self.assertEqual(malformed.context["notifications"].number, 1)
        self.assertEqual(out_of_range.context["notifications"].number, 2)

    def test_other_users_notifications_do_not_affect_page_counts(self):
        self.create_notifications(24)
        self.create_notifications(10, recipient=self.other)

        response = self.client.get(reverse("notification_list"))
        page = response.context["notifications"]

        self.assertEqual(page.paginator.count, 24)
        self.assertEqual(page.paginator.num_pages, 1)

    def test_mark_read_preserves_current_page(self):
        notifications = self.create_notifications(25)
        oldest = notifications[0]

        response = self.client.post(
            reverse("notification_mark_read", kwargs={"pk": oldest.pk}),
            {"page": "2"},
        )

        self.assertRedirects(
            response,
            reverse("notification_list") + "?page=2",
            fetch_redirect_response=False,
        )
        oldest.refresh_from_db()
        self.assertTrue(oldest.is_read)

    def test_mark_all_read_updates_notifications_across_pages_only_for_viewer(self):
        self.create_notifications(25)
        other_notification = self.create_notifications(1, recipient=self.other)[0]

        self.client.post(reverse("notification_mark_all_read"))

        self.assertFalse(
            Notification.objects.filter(
                recipient=self.recipient, read_at__isnull=True
            ).exists()
        )
        other_notification.refresh_from_db()
        self.assertFalse(other_notification.is_read)
