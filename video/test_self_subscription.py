from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel


class SelfSubscriptionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", password="password123"
        )
        self.viewer = User.objects.create_user(
            username="viewer", password="password123"
        )
        self.channel = Channel.objects.create(
            owner=self.owner,
            name="Owner Channel",
            description="A channel",
        )

    def test_owner_does_not_see_subscribe_control_on_own_channel(self):
        self.client.login(username="owner", password="password123")

        response = self.client.get(
            reverse("channel_detail", kwargs={"pk": self.channel.pk})
        )

        self.assertNotContains(response, ">Subscribe<")
        self.assertNotContains(response, ">Unsubscribe<")

    def test_owner_cannot_subscribe_by_posting_directly(self):
        self.client.login(username="owner", password="password123")

        response = self.client.post(
            reverse("subscribe", kwargs={"pk": self.channel.pk})
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.channel.subscribers.filter(pk=self.owner.pk).exists())

    def test_other_user_can_subscribe_and_unsubscribe(self):
        self.client.login(username="viewer", password="password123")
        url = reverse("subscribe", kwargs={"pk": self.channel.pk})

        subscribe_response = self.client.post(url)
        self.assertRedirects(
            subscribe_response,
            reverse("channel_detail", kwargs={"pk": self.channel.pk}),
        )
        self.assertTrue(self.channel.subscribers.filter(pk=self.viewer.pk).exists())

        unsubscribe_response = self.client.post(url)
        self.assertRedirects(
            unsubscribe_response,
            reverse("channel_detail", kwargs={"pk": self.channel.pk}),
        )
        self.assertFalse(self.channel.subscribers.filter(pk=self.viewer.pk).exists())
