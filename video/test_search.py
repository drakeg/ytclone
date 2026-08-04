from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel, Playlist, Video


class SearchDiscoveryTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="trailcreator", password="password123"
        )
        self.viewer = User.objects.create_user(
            username="viewer", password="password123"
        )
        self.category = Category.objects.create(
            name="Camping",
            description="Outdoor videos",
            thumbnail="categories/thumbnails/camping.jpg",
        )
        self.channel = Channel.objects.create(
            name="Trail Adventures",
            description="Camping and hiking trips",
            thumbnail="channels/thumbnails/trail.jpg",
            owner=self.creator,
        )
        self.low_view_video = Video.objects.create(
            title="Campground tour",
            description="A walk around the campground",
            thumbnail="videos/thumbnails/campground.jpg",
            video_file="videos/files/campground.mp4",
            views=10,
            author=self.creator,
            category=self.category,
        )
        self.high_view_video = Video.objects.create(
            title="Camping setup",
            description="Our complete RV campsite setup",
            thumbnail="videos/thumbnails/setup.jpg",
            video_file="videos/files/setup.mp4",
            views=200,
            author=self.creator,
            category=self.category,
        )
        self.high_view_video.likes.add(self.viewer)
        self.public_playlist = Playlist.objects.create(
            owner=self.creator,
            name="Camping Favorites",
            description="Favorite camping videos",
            visibility=Playlist.Visibility.PUBLIC,
        )
        self.unlisted_playlist = Playlist.objects.create(
            owner=self.creator,
            name="Camping Drafts",
            description="Unlisted camping collection",
            visibility=Playlist.Visibility.UNLISTED,
        )
        self.private_playlist = Playlist.objects.create(
            owner=self.creator,
            name="Camping Private",
            description="Private camping collection",
            visibility=Playlist.Visibility.PRIVATE,
        )

    def search(self, query="camping", sort="relevance"):
        return self.client.get(
            reverse("search"),
            {"query": query, "sort": sort},
        )

    def test_search_groups_videos_channels_and_public_playlists(self):
        response = self.search()

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.low_view_video, response.context["videos"])
        self.assertIn(self.high_view_video, response.context["videos"])
        self.assertIn(self.channel, response.context["channels"])
        self.assertIn(self.public_playlist, response.context["playlists"])

    def test_private_and_other_users_unlisted_playlists_are_hidden(self):
        response = self.search()

        playlists = list(response.context["playlists"])
        self.assertNotIn(self.private_playlist, playlists)
        self.assertNotIn(self.unlisted_playlist, playlists)

    def test_owner_can_find_own_unlisted_but_not_private_playlist(self):
        self.client.login(username="trailcreator", password="password123")

        response = self.search()

        playlists = list(response.context["playlists"])
        self.assertIn(self.public_playlist, playlists)
        self.assertIn(self.unlisted_playlist, playlists)
        self.assertNotIn(self.private_playlist, playlists)

    def test_video_search_matches_creator_and_category(self):
        creator_response = self.search(query="trailcreator")
        category_response = self.search(query="Camping")

        self.assertEqual(len(creator_response.context["videos"]), 2)
        self.assertEqual(len(category_response.context["videos"]), 2)

    def test_most_viewed_sort_orders_videos_by_views(self):
        response = self.search(sort="views")

        videos = list(response.context["videos"])
        self.assertEqual(videos[0], self.high_view_video)
        self.assertEqual(videos[1], self.low_view_video)

    def test_most_liked_sort_orders_videos_by_like_count(self):
        response = self.search(sort="likes")

        videos = list(response.context["videos"])
        self.assertEqual(videos[0], self.high_view_video)
        self.assertEqual(videos[0].like_count, 1)

    def test_invalid_sort_falls_back_to_relevance(self):
        response = self.search(sort="not-a-sort")

        self.assertEqual(response.context["selected_sort"], "relevance")

    def test_blank_query_returns_empty_grouped_results(self):
        response = self.search(query="   ")

        self.assertEqual(response.context["query"], "")
        self.assertEqual(list(response.context["videos"]), [])
        self.assertEqual(list(response.context["channels"]), [])
        self.assertEqual(list(response.context["playlists"]), [])
