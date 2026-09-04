from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Playlist, Video


class SearchPaginationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="pagination-creator", password="password123")
        for index in range(14):
            Video.objects.create(
                title=f"Pagination video {index:02d}",
                description="pagination result",
                thumbnail=f"videos/thumbnails/pagination-{index}.jpg",
                video_file=f"videos/files/pagination-{index}.mp4",
                author=self.creator,
                views=index,
            )
        for index in range(8):
            Channel.objects.create(
                name=f"Pagination Channel {index:02d}",
                description="pagination result",
                owner=self.creator,
            )
            Playlist.objects.create(
                owner=self.creator,
                name=f"Pagination Playlist {index:02d}",
                description="pagination result",
                visibility=Playlist.Visibility.PUBLIC,
            )

    def search(self, **params):
        query = {
            "query": "pagination",
            "sort": "views",
        }
        query.update(params)
        return self.client.get(reverse("search"), query)

    def test_first_page_bounds_each_result_group(self):
        response = self.search()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 12)
        self.assertEqual(len(response.context["channels"]), 6)
        self.assertEqual(len(response.context["playlists"]), 6)
        self.assertEqual(response.context["videos"].paginator.count, 14)
        self.assertEqual(response.context["channels"].paginator.count, 8)
        self.assertEqual(response.context["playlists"].paginator.count, 8)

    def test_each_result_group_pages_independently(self):
        response = self.search(video_page=2, channel_page=2, playlist_page=2)

        self.assertEqual(response.context["videos"].number, 2)
        self.assertEqual(response.context["channels"].number, 2)
        self.assertEqual(response.context["playlists"].number, 2)
        self.assertEqual(len(response.context["videos"]), 2)
        self.assertEqual(len(response.context["channels"]), 2)
        self.assertEqual(len(response.context["playlists"]), 2)

    def test_malformed_and_out_of_range_pages_are_bounded(self):
        response = self.search(video_page="not-a-number", channel_page=-4, playlist_page=999)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["videos"].number, 1)
        self.assertEqual(response.context["channels"].number, 1)
        self.assertEqual(response.context["playlists"].number, 2)

    def test_pagination_links_preserve_query_sort_and_other_page_numbers(self):
        response = self.search(video_page=1, channel_page=2, playlist_page=2)
        content = response.content.decode()

        self.assertIn("query=pagination", content)
        self.assertIn("sort=views", content)
        self.assertIn("channel_page=2", content)
        self.assertIn("playlist_page=2", content)
        self.assertIn("video_page=2", content)
        self.assertIn("Next videos", content)

    def test_blank_search_keeps_empty_page_objects(self):
        response = self.client.get(reverse("search"), {"query": "   "})

        self.assertEqual(list(response.context["videos"]), [])
        self.assertEqual(list(response.context["channels"]), [])
        self.assertEqual(list(response.context["playlists"]), [])
