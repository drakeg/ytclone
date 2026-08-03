from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Playlist, PlaylistItem, Video


class PlaylistTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.other_user = User.objects.create_user(username="other", password="password123")
        self.category = Category.objects.create(
            name="General",
            description="General videos",
            thumbnail="categories/thumbnails/general.jpg",
        )
        self.video = Video.objects.create(
            title="Playlist video",
            description="A video for playlist tests",
            thumbnail="videos/thumbnails/test.jpg",
            video_file="videos/files/test.mp4",
            author=self.owner,
            category=self.category,
        )

    def test_authenticated_user_can_create_playlist(self):
        self.client.login(username="owner", password="password123")
        response = self.client.post(
            reverse("playlist_create"),
            {
                "name": "Road Trips",
                "description": "Travel videos",
                "visibility": Playlist.Visibility.PUBLIC,
            },
        )

        playlist = Playlist.objects.get(owner=self.owner)
        self.assertRedirects(response, reverse("playlist_detail", kwargs={"pk": playlist.pk}))
        self.assertEqual(playlist.name, "Road Trips")

    def test_private_playlist_is_hidden_from_other_users(self):
        playlist = Playlist.objects.create(
            owner=self.owner,
            name="Private collection",
            visibility=Playlist.Visibility.PRIVATE,
        )
        self.client.login(username="other", password="password123")

        response = self.client.get(reverse("playlist_detail", kwargs={"pk": playlist.pk}))

        self.assertEqual(response.status_code, 404)

    def test_unlisted_playlist_is_available_by_direct_link(self):
        playlist = Playlist.objects.create(
            owner=self.owner,
            name="Shared link",
            visibility=Playlist.Visibility.UNLISTED,
        )

        response = self.client.get(reverse("playlist_detail", kwargs={"pk": playlist.pk}))

        self.assertEqual(response.status_code, 200)

    def test_public_playlist_appears_on_owner_profile(self):
        Playlist.objects.create(
            owner=self.owner,
            name="Public collection",
            visibility=Playlist.Visibility.PUBLIC,
        )
        Playlist.objects.create(
            owner=self.owner,
            name="Hidden collection",
            visibility=Playlist.Visibility.PRIVATE,
        )

        response = self.client.get(
            reverse("user_profile", kwargs={"username": self.owner.username})
        )

        playlists = list(response.context["public_playlists"])
        self.assertEqual([playlist.name for playlist in playlists], ["Public collection"])

    def test_owner_can_add_video_only_once(self):
        playlist = Playlist.objects.create(owner=self.owner, name="Favorites")
        self.client.login(username="owner", password="password123")
        url = reverse(
            "playlist_add_video",
            kwargs={"pk": playlist.pk, "video_pk": self.video.pk},
        )

        self.client.post(url)
        self.client.post(url)

        self.assertEqual(PlaylistItem.objects.filter(playlist=playlist).count(), 1)

    def test_other_user_cannot_modify_playlist(self):
        playlist = Playlist.objects.create(owner=self.owner, name="Owner only")
        self.client.login(username="other", password="password123")

        add_response = self.client.post(
            reverse(
                "playlist_add_video",
                kwargs={"pk": playlist.pk, "video_pk": self.video.pk},
            )
        )
        delete_response = self.client.post(
            reverse("playlist_delete", kwargs={"pk": playlist.pk})
        )

        self.assertEqual(add_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(Playlist.objects.filter(pk=playlist.pk).exists())
        self.assertFalse(PlaylistItem.objects.filter(playlist=playlist).exists())

    def test_playlist_mutations_reject_get_requests(self):
        playlist = Playlist.objects.create(owner=self.owner, name="POST only")
        item = PlaylistItem.objects.create(playlist=playlist, video=self.video, position=1)
        self.client.login(username="owner", password="password123")

        responses = [
            self.client.get(reverse("playlist_delete", kwargs={"pk": playlist.pk})),
            self.client.get(
                reverse(
                    "playlist_add_video",
                    kwargs={"pk": playlist.pk, "video_pk": self.video.pk},
                )
            ),
            self.client.get(
                reverse(
                    "playlist_remove_video",
                    kwargs={"pk": playlist.pk, "item_pk": item.pk},
                )
            ),
        ]

        self.assertTrue(all(response.status_code == 405 for response in responses))
