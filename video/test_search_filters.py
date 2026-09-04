from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Channel, Playlist, Video
from .services.search import search_content
from .shorts_models import VideoShort


class SearchFilterTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="filter-creator", password="password123"
        )
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Filter Channel",
            description="filter result",
        )
        self.playlist = Playlist.objects.create(
            owner=self.creator,
            name="Filter Playlist",
            description="filter result",
            visibility=Playlist.Visibility.PUBLIC,
        )

        self.recent_videos = []
        for index in range(13):
            self.recent_videos.append(
                Video.objects.create(
                    title=f"Filter standard {index:02d}",
                    description="filter result",
                    thumbnail=f"videos/thumbnails/filter-{index}.jpg",
                    video_file=f"videos/files/filter-{index}.mp4",
                    author=self.creator,
                    channel=self.channel,
                    views=index,
                )
            )

        self.old_video = Video.objects.create(
            title="Filter old standard",
            description="filter result",
            thumbnail="videos/thumbnails/filter-old.jpg",
            video_file="videos/files/filter-old.mp4",
            author=self.creator,
            channel=self.channel,
        )
        Video.objects.filter(pk=self.old_video.pk).update(
            pub_date=timezone.now() - timedelta(days=400)
        )
        self.old_video.refresh_from_db()

        self.short = Video.objects.create(
            title="Filter short",
            description="filter result",
            thumbnail="videos/thumbnails/filter-short.jpg",
            video_file="videos/files/filter-short.mp4",
            author=self.creator,
            channel=self.channel,
        )
        VideoShort.objects.create(video=self.short)

    def test_standard_video_filter_excludes_shorts(self):
        results = search_content(
            "filter", "relevance", content_filter="video"
        )

        videos = list(results.videos)
        self.assertIn(self.old_video, videos)
        self.assertNotIn(self.short, videos)
        self.assertEqual(len(videos), 14)

    def test_short_filter_returns_only_shorts(self):
        results = search_content(
            "filter", "relevance", content_filter="short"
        )

        self.assertEqual(list(results.videos), [self.short])

    def test_upload_date_filter_excludes_old_results(self):
        for upload_filter in ("today", "week", "month", "year"):
            with self.subTest(upload_filter=upload_filter):
                results = search_content(
                    "filter", "relevance", upload_date_filter=upload_filter
                )
                videos = list(results.videos)
                self.assertNotIn(self.old_video, videos)
                self.assertIn(self.short, videos)
                self.assertIn(self.recent_videos[0], videos)

    def test_invalid_filters_fall_back_to_defaults(self):
        results = search_content(
            "filter",
            "views",
            content_filter="invalid",
            upload_date_filter="never",
        )

        self.assertEqual(results.content_filter, "all")
        self.assertEqual(results.upload_date_filter, "any")
        self.assertIn(self.short, results.videos)
        self.assertIn(self.old_video, results.videos)

    def test_video_filters_do_not_change_channel_or_playlist_results(self):
        results = search_content(
            "filter",
            "relevance",
            content_filter="short",
            upload_date_filter="today",
        )

        self.assertIn(self.channel, results.channels)
        self.assertIn(self.playlist, results.playlists)

    def test_search_page_renders_filter_controls_and_selected_values(self):
        response = self.client.get(
            reverse("search"),
            {
                "query": "filter",
                "sort": "newest",
                "content": "short",
                "uploaded": "month",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_content_filter"], "short")
        self.assertEqual(response.context["selected_upload_date_filter"], "month")
        self.assertContains(response, 'id="search-content-filter"')
        self.assertContains(response, 'id="search-uploaded-filter"')
        self.assertContains(response, "Standard videos")
        self.assertContains(response, "This month")

    def test_pagination_links_preserve_filters(self):
        response = self.client.get(
            reverse("search"),
            {
                "query": "filter",
                "sort": "views",
                "content": "video",
                "uploaded": "year",
            },
        )
        content = response.content.decode()

        self.assertEqual(response.context["videos"].paginator.count, 13)
        self.assertIn("content=video", content)
        self.assertIn("uploaded=year", content)
        self.assertIn("video_page=2", content)
        self.assertIn("Next videos", content)
