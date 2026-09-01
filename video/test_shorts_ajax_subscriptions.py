from pathlib import Path

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
        self.assertContains(response, "video/shorts_subscription_ajax.js")

    def test_dedicated_controller_wires_subscription_forms_to_ajax(self):
        script = Path("video/static/video/shorts_subscription_ajax.js").read_text(encoding="utf-8")
        self.assertIn('"[data-short-subscribe-form]"', script)
        self.assertIn('"X-Requested-With": "XMLHttpRequest"', script)
        self.assertIn("syncSubscription(form, await response.json())", script)
        self.assertIn('feed.addEventListener("submit"', script)
        self.assertIn("new FormData(form)", script)

    def test_general_feed_controller_no_longer_owns_subscriptions(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertNotIn("data-short-subscribe-form", script)
        self.assertNotIn("submitSubscription", script)
        self.assertNotIn("syncSubscription", script)
        self.assertNotIn("subscribeForms", script)

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
