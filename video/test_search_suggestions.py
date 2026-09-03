from pathlib import Path

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Playlist, Video
from .services.search import search_suggestions


class SearchSuggestionsTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="suggestion-creator", password="password123"
        )
        self.viewer = User.objects.create_user(
            username="suggestion-viewer", password="password123"
        )
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Trail Suggestions",
            description="",
        )
        self.public_video = Video.objects.create(
            title="Trail Camera Setup",
            description="",
            thumbnail="videos/thumbnails/trail.jpg",
            video_file="videos/files/trail.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
            views=25,
        )
        self.private_video = Video.objects.create(
            title="Trail Private Draft",
            description="",
            thumbnail="videos/thumbnails/private.jpg",
            video_file="videos/files/private.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PRIVATE,
        )
        self.public_playlist = Playlist.objects.create(
            owner=self.creator,
            name="Trail Favorites",
            description="",
            visibility=Playlist.Visibility.PUBLIC,
        )
        self.unlisted_playlist = Playlist.objects.create(
            owner=self.creator,
            name="Trail Unlisted Notes",
            description="",
            visibility=Playlist.Visibility.UNLISTED,
        )
        self.private_playlist = Playlist.objects.create(
            owner=self.creator,
            name="Trail Private Notes",
            description="",
            visibility=Playlist.Visibility.PRIVATE,
        )

    def test_short_queries_return_no_suggestions(self):
        self.assertEqual(search_suggestions("", AnonymousUser()), [])
        self.assertEqual(search_suggestions("t", AnonymousUser()), [])

    def test_anonymous_suggestions_respect_visibility(self):
        suggestions = search_suggestions("Trail", AnonymousUser())

        self.assertIn(self.public_video.title, suggestions)
        self.assertIn(self.channel.name, suggestions)
        self.assertIn(self.public_playlist.name, suggestions)
        self.assertNotIn(self.private_video.title, suggestions)
        self.assertNotIn(self.unlisted_playlist.name, suggestions)
        self.assertNotIn(self.private_playlist.name, suggestions)

    def test_owner_can_receive_own_unlisted_playlist_suggestion(self):
        suggestions = search_suggestions("Unlisted", self.creator)

        self.assertIn(self.unlisted_playlist.name, suggestions)
        self.assertNotIn(self.private_playlist.name, suggestions)

    def test_suggestions_are_deduplicated_and_bounded(self):
        Channel.objects.create(
            owner=self.viewer,
            name=self.public_video.title,
            description="",
        )
        for index in range(10):
            Video.objects.create(
                title=f"Trail Extra {index}",
                description="",
                thumbnail=f"videos/thumbnails/trail-{index}.jpg",
                video_file=f"videos/files/trail-{index}.mp4",
                author=self.creator,
                channel=self.channel,
                publication_status=Video.PublicationStatus.PUBLISHED,
                views=index,
            )

        suggestions = search_suggestions("Trail", AnonymousUser(), limit=8)

        self.assertLessEqual(len(suggestions), 8)
        self.assertEqual(len(suggestions), len({value.casefold() for value in suggestions}))

    def test_json_endpoint_returns_service_results(self):
        response = self.client.get(reverse("search_suggestions"), {"query": "Trail"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["suggestions"],
            search_suggestions("Trail", AnonymousUser()),
        )

    def test_base_search_inputs_are_progressively_enhanced(self):
        response = self.client.get(reverse("video_list"))

        self.assertContains(response, 'data-search-suggestions="/videos/search/suggestions/"', count=2)
        self.assertContains(response, 'list="site-search-suggestions"')
        self.assertContains(response, 'list="mobile-site-search-suggestions"')
        self.assertContains(response, "video/search_suggestions.js")

    def test_controller_debounces_ignores_stale_responses_and_submits_selection(self):
        script = Path("video/static/video/search_suggestions.js").read_text(encoding="utf-8")

        self.assertIn("window.setTimeout", script)
        self.assertIn("currentRequest !== requestNumber", script)
        self.assertIn('url.searchParams.set("query", query)', script)
        self.assertIn("input.form?.requestSubmit()", script)
