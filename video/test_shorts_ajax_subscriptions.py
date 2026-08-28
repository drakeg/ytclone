from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsAjaxSubscriptionUiTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="short-sub-creator", password="password123")
        self.viewer = User.objects.create_user(username="short-sub-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Short Subscribe Channel", description="")
        self.video = Video.objects.create(
            title="Subscribe Short",
            description="Subscription UI test",
            thumbnail="videos/thumbnails/subscribe.jpg",
            video_file="videos/files/subscribe.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)
        self.client.force_login(self.viewer)

    def test_feed_marks_subscription_form_for_progressive_enhancement(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-short-subscribe-form")
        self.assertContains(response, "data-short-subscribe")
        self.assertContains(response, 'aria-pressed="false"')
        self.assertContains(response, "Could not update subscription.")

    def test_feed_wires_subscription_forms_to_ajax_handler(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "submitSubscription(form)")
        self.assertContains(response, "syncSubscription(form,await response.json())")
        self.assertContains(response, "'X-Requested-With':'XMLHttpRequest'")
        self.assertContains(response, "subscribeForms.forEach")

    def test_subscribed_state_renders_before_javascript_runs(self):
        self.channel.subscribers.add(self.viewer)
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, ">Subscribed</button>")
        self.assertContains(response, 'data-short-subscribe aria-pressed="true"')
        self.assertContains(response, "btn-outline-secondary")

    def test_form_keeps_safe_redirect_fallback(self):
        response = self.client.get(reverse("shorts_feed"))
        expected_next = f'{reverse("shorts_feed")}#short-{self.video.pk}'
        self.assertContains(response, f'name="next" value="{expected_next}"')
        self.assertContains(response, f'action="{reverse("subscribe", args=[self.channel.pk])}"')
