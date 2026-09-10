from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Channel, Video
from .moderation_models import ChannelModerationState
from .services.subscriptions import SUBSCRIPTIONS_FEED_LIMIT, get_subscriptions_feed


class SubscriptionsFeedTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username="viewer", password="password")
        self.creator = User.objects.create_user(username="creator", password="password")
        self.other_creator = User.objects.create_user(username="other", password="password")
        self.channel = Channel.objects.create(name="Followed channel", description="Followed", owner=self.creator)
        self.other_channel = Channel.objects.create(name="Other channel", description="Other", owner=self.other_creator)
        self.channel.subscribers.add(self.viewer)

    def make_video(self, *, title, channel=None, author=None, status=Video.PublicationStatus.PUBLISHED):
        channel = channel or self.channel
        author = author or channel.owner
        return Video.objects.create(
            title=title,
            description="Description",
            thumbnail="videos/thumbnails/test.jpg",
            video_file="videos/files/test.mp4",
            author=author,
            channel=channel,
            publication_status=status,
        )

    def test_page_requires_login(self):
        response = self.client.get(reverse("subscriptions_feed"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_feed_contains_only_available_followed_channels(self):
        suspended = Channel.objects.create(name="Suspended", description="Hidden", owner=self.other_creator)
        suspended.subscribers.add(self.viewer)
        ChannelModerationState.objects.create(channel=suspended)

        feed = get_subscriptions_feed(self.viewer)

        self.assertEqual(list(feed.channels), [self.channel])
        self.assertNotIn(self.other_channel, feed.channels)

    def test_feed_uses_video_visibility_and_orders_newest_first(self):
        older = self.make_video(title="Older")
        newer = self.make_video(title="Newer")
        hidden = self.make_video(title="Draft", status=Video.PublicationStatus.DRAFT)
        other = self.make_video(title="Not followed", channel=self.other_channel)
        Video.objects.filter(pk=older.pk).update(pub_date=timezone.now() - timedelta(days=1))
        Video.objects.filter(pk=newer.pk).update(pub_date=timezone.now())

        feed = get_subscriptions_feed(self.viewer)
        videos = list(feed.videos)

        self.assertEqual(videos, [newer, older])
        self.assertNotIn(hidden, videos)
        self.assertNotIn(other, videos)

    def test_optional_service_limit_remains_supported(self):
        for index in range(SUBSCRIPTIONS_FEED_LIMIT + 3):
            self.make_video(title=f"Video {index}")

        self.assertEqual(
            len(list(get_subscriptions_feed(self.viewer, limit=SUBSCRIPTIONS_FEED_LIMIT).videos)),
            SUBSCRIPTIONS_FEED_LIMIT,
        )

    def test_page_paginates_older_subscription_videos(self):
        for index in range(SUBSCRIPTIONS_FEED_LIMIT + 3):
            self.make_video(title=f"Video {index}")

        self.client.force_login(self.viewer)
        first = self.client.get(reverse("subscriptions_feed"))
        second = self.client.get(reverse("subscriptions_feed"), {"page": 2})

        self.assertEqual(len(first.context["videos"]), SUBSCRIPTIONS_FEED_LIMIT)
        self.assertEqual(first.context["videos"].paginator.num_pages, 2)
        self.assertEqual(len(second.context["videos"]), 3)
        self.assertContains(first, "Page 1 of 2")
        self.assertContains(second, "Page 2 of 2")

    def test_channel_filter_only_accepts_followed_available_channels(self):
        second_followed = Channel.objects.create(name="Second followed", description="", owner=self.other_creator)
        second_followed.subscribers.add(self.viewer)
        first_video = self.make_video(title="First channel video")
        second_video = self.make_video(title="Second channel video", channel=second_followed)
        unfiltered = get_subscriptions_feed(self.viewer)
        filtered = get_subscriptions_feed(self.viewer, channel=second_followed.pk)
        invalid = get_subscriptions_feed(self.viewer, channel=self.other_channel.pk)

        self.assertIn(first_video, unfiltered.videos)
        self.assertIn(second_video, unfiltered.videos)
        self.assertEqual(list(filtered.videos), [second_video])
        self.assertEqual(filtered.selected_channel, second_followed)
        self.assertIsNone(invalid.selected_channel)
        self.assertIn(first_video, invalid.videos)
        self.assertIn(second_video, invalid.videos)

    def test_channel_filter_is_preserved_through_pagination(self):
        second_followed = Channel.objects.create(name="Second followed", description="", owner=self.other_creator)
        second_followed.subscribers.add(self.viewer)
        for index in range(SUBSCRIPTIONS_FEED_LIMIT + 1):
            self.make_video(title=f"Second {index}", channel=second_followed)
        self.make_video(title="Different channel")

        self.client.force_login(self.viewer)
        response = self.client.get(reverse("subscriptions_feed"), {"channel": second_followed.pk})

        self.assertEqual(response.context["selected_channel"], second_followed)
        self.assertEqual(response.context["videos"].paginator.count, SUBSCRIPTIONS_FEED_LIMIT + 1)
        self.assertContains(response, f"channel={second_followed.pk}&amp;page=2")
        self.assertNotContains(response, "Different channel")

    def test_page_distinguishes_subscription_and_video_empty_states(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("subscriptions_feed"))
        self.assertContains(response, "Nothing new to watch yet")
        self.assertNotContains(response, "You are not following any channels yet")

        self.channel.subscribers.remove(self.viewer)
        response = self.client.get(reverse("subscriptions_feed"))
        self.assertContains(response, "You are not following any channels yet")

    def test_authenticated_navigation_links_to_subscriptions(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("video_list"))
        self.assertContains(response, f'href="{reverse("subscriptions_feed")}"')
        self.assertContains(response, ">Subscriptions</span>")
