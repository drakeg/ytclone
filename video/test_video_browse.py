from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort
from .services.video_browse import browse_videos


class VideoBrowseTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="browse-creator", password="password123")
        self.viewer = User.objects.create_user(username="browse-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Browse Channel", description="Browse")

    def video(self, title, *, views=0, status=Video.PublicationStatus.PUBLISHED, audience=Video.Audience.EVERYONE):
        return Video.objects.create(
            title=title,
            description=title,
            thumbnail=f"videos/thumbnails/{title}.jpg",
            video_file=f"videos/files/{title}.mp4",
            author=self.creator,
            channel=self.channel,
            views=views,
            publication_status=status,
            audience=audience,
        )

    def test_browse_reuses_visibility_and_excludes_shorts(self):
        public = self.video("public")
        self.video("draft", status=Video.PublicationStatus.DRAFT)
        self.video("members", audience=Video.Audience.MEMBERS_ONLY)
        short = self.video("short")
        VideoShort.objects.create(video=short)

        videos, selected_sort = browse_videos(self.viewer)

        self.assertEqual(selected_sort, "newest")
        self.assertEqual(list(videos), [public])

    def test_sort_orders_are_deterministic(self):
        first = self.video("first", views=5)
        second = self.video("second", views=30)
        third = self.video("third", views=10)
        first.likes.add(self.viewer)
        third.likes.add(self.viewer, self.creator)

        newest, _ = browse_videos(self.viewer, "newest")
        viewed, _ = browse_videos(self.viewer, "views")
        liked, _ = browse_videos(self.viewer, "likes")

        self.assertEqual(list(newest), [third, second, first])
        self.assertEqual(list(viewed), [second, third, first])
        self.assertEqual(list(liked), [third, first, second])

    def test_invalid_sort_falls_back_to_newest(self):
        self.video("video")
        _videos, selected_sort = browse_videos(self.viewer, "unknown")
        self.assertEqual(selected_sort, "newest")

    def test_browse_page_is_bounded_and_paginates(self):
        for number in range(26):
            self.video(f"video-{number}")

        first = self.client.get(reverse("video_browse"), {"sort": "newest"})
        second = self.client.get(reverse("video_browse"), {"sort": "newest", "page": 2})

        self.assertEqual(len(first.context["videos"]), 24)
        self.assertEqual(len(second.context["videos"]), 2)
        self.assertContains(first, "Page 1 of 2")
        self.assertContains(first, "sort=newest")
        self.assertContains(first, "uploaded=any")
        self.assertContains(first, "page=2")

    def test_bad_page_values_resolve_safely(self):
        for number in range(26):
            self.video(f"video-{number}")

        malformed = self.client.get(reverse("video_browse"), {"page": "nope"})
        negative = self.client.get(reverse("video_browse"), {"page": -3})
        too_high = self.client.get(reverse("video_browse"), {"page": 999})

        self.assertEqual(malformed.context["videos"].number, 1)
        self.assertEqual(negative.context["videos"].number, 2)
        self.assertEqual(too_high.context["videos"].number, 2)

    def test_homepage_shelves_link_to_matching_browse_orders(self):
        response = self.client.get(reverse("video_list"))

        browse = reverse("video_browse")
        self.assertContains(response, f'{browse}?sort=newest')
        self.assertContains(response, f'{browse}?sort=views')
        self.assertContains(response, f'{browse}?sort=likes')
