from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Playlist, PlaylistItem, Video
from .services.watch_later import WATCH_LATER_NAME, get_watch_later_playlist, watch_later_videos


class WatchLaterTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username="viewer", password="password")
        self.other = User.objects.create_user(username="other", password="password")
        self.creator = User.objects.create_user(username="creator", password="password")
        self.video = Video.objects.create(
            title="Save me",
            description="Description",
            thumbnail="videos/thumbnails/test.jpg",
            video_file="videos/files/test.mp4",
            author=self.creator,
        )

    def test_page_and_mutations_require_login(self):
        self.assertEqual(self.client.get(reverse("watch_later")).status_code, 302)
        self.assertEqual(self.client.post(reverse("watch_later_add", args=[self.video.pk])).status_code, 302)
        self.assertIsNone(get_watch_later_playlist(self.viewer))

    def test_add_is_idempotent_and_collection_is_private(self):
        self.client.force_login(self.viewer)
        url = reverse("watch_later_add", args=[self.video.pk])

        self.client.post(url)
        self.client.post(url)

        playlist = get_watch_later_playlist(self.viewer)
        self.assertEqual(playlist.name, WATCH_LATER_NAME)
        self.assertEqual(playlist.visibility, Playlist.Visibility.PRIVATE)
        self.assertEqual(PlaylistItem.objects.filter(playlist=playlist, video=self.video).count(), 1)

    def test_remove_only_changes_current_viewers_collection(self):
        viewer_playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        other_playlist = Playlist.objects.create(owner=self.other, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        PlaylistItem.objects.create(playlist=viewer_playlist, video=self.video)
        PlaylistItem.objects.create(playlist=other_playlist, video=self.video)
        self.client.force_login(self.viewer)

        self.client.post(reverse("watch_later_remove", args=[self.video.pk]))

        self.assertFalse(PlaylistItem.objects.filter(playlist=viewer_playlist, video=self.video).exists())
        self.assertTrue(PlaylistItem.objects.filter(playlist=other_playlist, video=self.video).exists())

    def test_queue_uses_video_visibility_rules(self):
        hidden = Video.objects.create(
            title="Hidden",
            description="Description",
            thumbnail="videos/thumbnails/hidden.jpg",
            video_file="videos/files/hidden.mp4",
            author=self.creator,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        PlaylistItem.objects.create(playlist=playlist, video=self.video, position=0)
        PlaylistItem.objects.create(playlist=playlist, video=hidden, position=1)

        self.assertEqual(list(watch_later_videos(self.viewer)), [self.video])

    def test_page_renders_saved_video_and_remove_action(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"))

        self.assertContains(response, "Save me")
        self.assertContains(response, "Remove from Watch Later")
        self.assertContains(response, reverse("watch_later_remove", args=[self.video.pk]))

    def test_video_cards_offer_watch_later_action_to_signed_in_viewer(self):
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("video_list"))

        self.assertContains(response, "Watch Later")
        self.assertContains(response, reverse("watch_later_add", args=[self.video.pk]))

    def test_navigation_links_to_watch_later(self):
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("video_list"))

        self.assertContains(response, f'href="{reverse("watch_later")}"')
