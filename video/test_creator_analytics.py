from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Channel, Video
from .services.analytics import get_creator_analytics


class CreatorAnalyticsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator", password="password123"
        )
        self.other_creator = User.objects.create_user(
            username="other-creator", password="password123"
        )
        self.viewer_one = User.objects.create_user(
            username="viewer-one", password="password123"
        )
        self.viewer_two = User.objects.create_user(
            username="viewer-two", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General videos",
            thumbnail="categories/thumbnails/general.jpg",
        )

    def create_video(self, author, title, views=0, minutes_ago=0):
        video = Video.objects.create(
            title=title,
            description=f"Description for {title}",
            thumbnail=f"videos/thumbnails/{title}.jpg",
            video_file=f"videos/files/{title}.mp4",
            views=views,
            author=author,
            category=self.category,
        )
        Video.objects.filter(pk=video.pk).update(
            pub_date=timezone.now() - timedelta(minutes=minutes_ago)
        )
        video.refresh_from_db()
        return video

    def create_channel(self, owner, name):
        return Channel.objects.create(
            owner=owner,
            name=name,
            description=f"Description for {name}",
            thumbnail=f"channels/thumbnails/{name}.jpg",
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("creator_analytics"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_empty_dashboard_renders_zeroes_and_empty_state(self):
        self.client.login(username="creator", password="password123")

        response = self.client.get(reverse("creator_analytics"))

        self.assertEqual(response.status_code, 200)
        analytics = response.context["analytics"]
        self.assertEqual(analytics.video_count, 0)
        self.assertEqual(analytics.total_views, 0)
        self.assertEqual(analytics.total_likes, 0)
        self.assertEqual(analytics.total_dislikes, 0)
        self.assertEqual(analytics.subscriber_count, 0)
        self.assertContains(response, "Upload a video to start seeing performance data.")

    def test_summary_totals_include_only_current_creators_videos(self):
        first = self.create_video(self.creator, "First", views=100)
        second = self.create_video(self.creator, "Second", views=25)
        other = self.create_video(self.other_creator, "Other", views=1000)
        first.likes.add(self.viewer_one, self.viewer_two)
        second.likes.add(self.viewer_one)
        second.dislikes.add(self.viewer_two)
        other.likes.add(self.viewer_one, self.viewer_two)

        analytics = get_creator_analytics(self.creator)

        self.assertEqual(analytics.video_count, 2)
        self.assertEqual(analytics.total_views, 125)
        self.assertEqual(analytics.total_likes, 3)
        self.assertEqual(analytics.total_dislikes, 1)

    def test_subscribers_are_unique_across_creators_channels(self):
        first = self.create_channel(self.creator, "First channel")
        second = self.create_channel(self.creator, "Second channel")
        other = self.create_channel(self.other_creator, "Other channel")
        first.subscribers.add(self.viewer_one, self.viewer_two)
        second.subscribers.add(self.viewer_one)
        other.subscribers.add(self.viewer_one)

        analytics = get_creator_analytics(self.creator)

        self.assertEqual(analytics.subscriber_count, 2)

    def test_video_performance_is_ordered_by_views_then_likes(self):
        low = self.create_video(self.creator, "Low", views=5)
        tied_without_like = self.create_video(
            self.creator, "Tied without like", views=20, minutes_ago=1
        )
        tied_with_like = self.create_video(
            self.creator, "Tied with like", views=20, minutes_ago=10
        )
        tied_with_like.likes.add(self.viewer_one)

        videos = list(get_creator_analytics(self.creator).videos)

        self.assertEqual(videos, [tied_with_like, tied_without_like, low])
        self.assertEqual(videos[0].like_count, 1)
        self.assertEqual(videos[0].dislike_count, 0)

    def test_dashboard_does_not_render_another_creators_video(self):
        own = self.create_video(self.creator, "Own video", views=10)
        other = self.create_video(self.other_creator, "Secret performance", views=500)
        self.client.login(username="creator", password="password123")

        response = self.client.get(reverse("creator_analytics"))

        self.assertContains(response, own.title)
        self.assertNotContains(response, other.title)

    def test_authenticated_navigation_links_to_creator_analytics(self):
        self.create_channel(self.creator, "Creator channel")
        self.client.login(username="creator", password="password123")

        response = self.client.get(reverse("video_list"))

        self.assertContains(response, reverse("creator_analytics"))
        self.assertContains(response, "Creator Analytics")
