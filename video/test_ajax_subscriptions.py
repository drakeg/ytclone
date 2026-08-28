from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Notification


class AjaxSubscriptionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="ajax-sub-owner", password="password123")
        self.viewer = User.objects.create_user(username="ajax-sub-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.owner, name="AJAX Subscription Channel", description="")
        self.client.force_login(self.viewer)

    def ajax_post(self):
        return self.client.post(
            reverse("subscribe", args=[self.channel.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

    def test_ajax_subscribe_returns_state_and_count(self):
        response = self.ajax_post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"subscribed": True, "subscriber_count": 1})
        self.assertTrue(self.channel.subscribers.filter(pk=self.viewer.pk).exists())
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.owner,
                actor=self.viewer,
                kind=Notification.Kind.SUBSCRIPTION,
            ).exists()
        )

    def test_ajax_unsubscribe_returns_state_and_count(self):
        self.channel.subscribers.add(self.viewer)
        response = self.ajax_post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"subscribed": False, "subscriber_count": 0})
        self.assertFalse(self.channel.subscribers.filter(pk=self.viewer.pk).exists())

    def test_regular_post_preserves_safe_redirect_behavior(self):
        response = self.client.post(
            reverse("subscribe", args=[self.channel.pk]),
            {"next": "/videos/shorts/#short-42"},
        )
        self.assertRedirects(response, "/videos/shorts/#short-42", fetch_redirect_response=False)

    def test_ajax_self_subscription_remains_forbidden(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("subscribe", args=[self.channel.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 403)
