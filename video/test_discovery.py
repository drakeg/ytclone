from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Playlist, Video, WatchHistory
from .services.discovery import DISCOVERY_SECTION_LIMIT, get_discovery_sections


class HomepageDiscoveryTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator", password="password123"
        )
        self.viewer = User.objects.create_user(
            username="viewer", password="password123"
        )
        self.other_viewer = User.objects.create_user(
            username="other-viewer", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General videos",
            thumbnail="categories/thumbnails/general.jpg",
        )

    def create_video(self, title, views=0, published_minutes_ago=0):
        video = Video.objects.create(
            title=title,
            description=f"Description for {title}",
            thumbnail=f"videos/thumbnails/{title}.jpg",
            video_file=f"videos/files/{title}.mp4",
            views=views,
            author=self.creator,
            category=self.category,
        )
        Video.objects.filter(pk=video.pk).update(
            pub_date=timezone.now() - timedelta(minutes=published_minutes_ago)
        )
        video.refresh_from_db()
        return video

    def test_empty_homepage_renders_all_public_sections(self):
        response = self.client.get(reverse("video_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Newest videos")
        self.assertContains(response, "Most viewed")
        self.assertContains(response, "Most liked")
        self.assertContains(response, "No videos to show yet.", count=3)
        self.assertContains(response, "No public playlists to show yet.")

    def test_sections_order_videos_by_their_metric(self):
        older_popular = self.create_video(
            "older-popular", views=500, published_minutes_ago=30
        )
        newest = self.create_video("newest", views=5, published_minutes_ago=1)
        most_liked = self.create_video(
            "most-liked", views=10, published_minutes_ago=15
        )
        most_liked.likes.add(self.viewer, self.other_viewer)

        sections = get_discovery_sections(self.viewer)

        self.assertEqual(sections.newest_videos[0], newest)
        self.assertEqual(sections.most_viewed_videos[0], older_popular)
        self.assertEqual(sections.most_liked_videos[0], most_liked)
        self.assertEqual(sections.most_liked_videos[0].like_count, 2)

    def test_each_discovery_section_is_bounded(self):
        for number in range(DISCOVERY_SECTION_LIMIT + 2):
            self.create_video(f"video-{number}", views=number)
            Playlist.objects.create(
                owner=self.creator,
                name=f"Public {number}",
                visibility=Playlist.Visibility.PUBLIC,
            )

        sections = get_discovery_sections(self.viewer)

        self.assertEqual(len(sections.newest_videos), DISCOVERY_SECTION_LIMIT)
        self.assertEqual(len(sections.most_viewed_videos), DISCOVERY_SECTION_LIMIT)
        self.assertEqual(len(sections.most_liked_videos), DISCOVERY_SECTION_LIMIT)
        self.assertEqual(len(sections.public_playlists), DISCOVERY_SECTION_LIMIT)

    def test_only_public_playlists_are_discovered(self):
        public = Playlist.objects.create(
            owner=self.creator,
            name="Public",
            visibility=Playlist.Visibility.PUBLIC,
        )
        Playlist.objects.create(
            owner=self.viewer,
            name="Viewer private",
            visibility=Playlist.Visibility.PRIVATE,
        )
        Playlist.objects.create(
            owner=self.viewer,
            name="Viewer unlisted",
            visibility=Playlist.Visibility.UNLISTED,
        )

        sections = get_discovery_sections(self.viewer)

        self.assertEqual(list(sections.public_playlists), [public])

    def test_anonymous_homepage_omits_recently_watched(self):
        video = self.create_video("watched")
        WatchHistory.objects.create(user=self.viewer, video=video)

        response = self.client.get(reverse("video_list"))

        self.assertNotContains(response, "Recently watched")
        self.assertEqual(list(response.context["sections"].recently_watched_videos), [])

    def test_recently_watched_is_isolated_and_ordered_for_current_user(self):
        older = self.create_video("older")
        newer = self.create_video("newer")
        other_users_video = self.create_video("other-users-video")
        older_entry = WatchHistory.objects.create(user=self.viewer, video=older)
        WatchHistory.objects.create(user=self.viewer, video=newer)
        WatchHistory.objects.create(user=self.other_viewer, video=other_users_video)
        WatchHistory.objects.filter(pk=older_entry.pk).update(
            watched_at=timezone.now() - timedelta(days=1)
        )
        self.client.login(username="viewer", password="password123")

        response = self.client.get(reverse("video_list"))

        recent = list(response.context["sections"].recently_watched_videos)
        self.assertEqual(recent, [newer, older])
        self.assertNotIn(other_users_video, recent)
        self.assertContains(response, "Recently watched")

    def test_repeat_views_produce_one_recently_watched_video(self):
        video = self.create_video("repeat")
        WatchHistory.objects.create(user=self.viewer, video=video)
        self.client.login(username="viewer", password="password123")

        sections = get_discovery_sections(self.viewer)

        self.assertEqual(list(sections.recently_watched_videos), [video])
