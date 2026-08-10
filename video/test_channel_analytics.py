from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel, Video
from .services.analytics import get_channel_analytics


class ChannelAnalyticsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.category = Category.objects.create(name="General", description="General", thumbnail="categories/general.jpg")
        self.channel = Channel.objects.create(name="Primary", description="Primary", thumbnail="channels/primary.jpg", owner=self.owner)
        self.second_channel = Channel.objects.create(name="Second", description="Second", thumbnail="channels/second.jpg", owner=self.owner)

    def video(self, title, channel, views=0):
        return Video.objects.create(title=title, description=title, thumbnail=f"videos/{title}.jpg", video_file=f"videos/{title}.mp4", author=self.owner, channel=channel, category=self.category, views=views)

    def test_anonymous_is_redirected_and_non_owner_gets_404(self):
        url = reverse("channel_analytics", kwargs={"pk": self.channel.pk})
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.login(username="other", password="password123")
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_totals_are_scoped_to_channel(self):
        own = self.video("Own", self.channel, views=100)
        other = self.video("Other", self.second_channel, views=900)
        legacy = self.video("Legacy", None, views=800)
        own.likes.add(self.viewer)
        own.dislikes.add(self.other)
        other.likes.add(self.viewer)
        self.channel.subscribers.add(self.viewer, self.other)

        analytics = get_channel_analytics(self.channel)

        self.assertEqual(analytics.video_count, 1)
        self.assertEqual(analytics.total_views, 100)
        self.assertEqual(analytics.total_likes, 1)
        self.assertEqual(analytics.total_dislikes, 1)
        self.assertEqual(analytics.subscriber_count, 2)
        self.assertEqual(list(analytics.videos), [own])
        self.assertNotIn(legacy, analytics.videos)

    def test_videos_are_ordered_by_views_then_likes(self):
        low = self.video("Low", self.channel, views=5)
        tied_plain = self.video("Plain", self.channel, views=20)
        tied_liked = self.video("Liked", self.channel, views=20)
        tied_liked.likes.add(self.viewer)
        self.assertEqual(list(get_channel_analytics(self.channel).videos), [tied_liked, tied_plain, low])

    def test_empty_channel_renders_zeroes_and_empty_state(self):
        self.client.login(username="owner", password="password123")
        response = self.client.get(reverse("channel_analytics", kwargs={"pk": self.channel.pk}))
        self.assertEqual(response.context["analytics"].video_count, 0)
        self.assertContains(response, "This channel has no videos yet.")

    def test_owner_sees_analytics_link_on_channel_page(self):
        self.client.login(username="owner", password="password123")
        response = self.client.get(reverse("channel_detail", kwargs={"pk": self.channel.pk}))
        self.assertContains(response, reverse("channel_analytics", kwargs={"pk": self.channel.pk}))

    def test_non_owner_does_not_see_analytics_link(self):
        self.client.login(username="other", password="password123")
        response = self.client.get(reverse("channel_detail", kwargs={"pk": self.channel.pk}))
        self.assertNotContains(response, reverse("channel_analytics", kwargs={"pk": self.channel.pk}))
