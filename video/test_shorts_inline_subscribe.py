from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsInlineSubscribeTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="short-owner", password="password123")
        self.viewer = User.objects.create_user(username="short-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Inline Subscribe Channel", description="")
        self.short = Video.objects.create(
            title="Inline Subscribe Short",
            description="Short used to test feed subscriptions",
            thumbnail="videos/thumbnails/inline-subscribe.jpg",
            video_file="videos/files/inline-subscribe.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.short)

    def test_authenticated_viewer_sees_subscribe_control(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, reverse("subscribe", args=[self.channel.pk]))
        self.assertContains(response, 'data-short-subscribe')
        self.assertContains(response, '>Subscribe</button>')

    def test_subscribed_viewer_sees_subscribed_state(self):
        self.channel.subscribers.add(self.viewer)
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, '>Subscribed</button>')

    def test_creator_does_not_see_self_subscribe_control(self):
        self.client.force_login(self.creator)
        response = self.client.get(reverse("shorts_feed"))
        self.assertNotContains(response, '<form method="post" action="/videos/channels/')
        self.assertNotContains(response, '<button class="btn btn-sm btn-primary" type="submit" data-short-subscribe')
        self.assertNotContains(response, '<button class="btn btn-sm btn-outline-secondary" type="submit" data-short-subscribe')

    def test_subscription_toggle_can_return_to_short_feed_anchor(self):
        self.client.force_login(self.viewer)
        next_url = reverse("shorts_feed") + f"#short-{self.short.pk}"
        response = self.client.post(
            reverse("subscribe", args=[self.channel.pk]),
            {"next": next_url},
        )
        self.assertRedirects(response, next_url, fetch_redirect_response=False)
        self.assertTrue(self.channel.subscribers.filter(pk=self.viewer.pk).exists())

    def test_subscription_toggle_rejects_external_next_url(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("subscribe", args=[self.channel.pk]),
            {"next": "https://example.com/escape"},
        )
        self.assertRedirects(
            response,
            reverse("channel_detail", args=[self.channel.pk]),
            fetch_redirect_response=False,
        )
