from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Playlist, PlaylistItem, Video
from .playlist_views import PLAYLIST_PAGE_SIZE


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

    def make_video(self, title, *, status=Video.PublicationStatus.PUBLISHED):
        return Video.objects.create(
            title=title,
            description=f"Description for {title}",
            thumbnail=f"videos/thumbnails/{title}.jpg",
            video_file=f"videos/files/{title}.mp4",
            author=self.owner,
            category=self.category,
            publication_status=status,
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

    def test_playlist_detail_paginates_visible_items_in_playlist_order(self):
        playlist = Playlist.objects.create(
            owner=self.owner,
            name="Long playlist",
            visibility=Playlist.Visibility.PUBLIC,
        )
        videos = []
        for index in range(PLAYLIST_PAGE_SIZE + 2):
            video = self.make_video(f"Video {index:02d}")
            videos.append(video)
            PlaylistItem.objects.create(playlist=playlist, video=video, position=index)

        first_page = self.client.get(reverse("playlist_detail", args=[playlist.pk]))
        second_page = self.client.get(reverse("playlist_detail", args=[playlist.pk]), {"page": 2})

        self.assertEqual(len(first_page.context["visible_items"]), PLAYLIST_PAGE_SIZE)
        self.assertEqual(first_page.context["visible_items"].paginator.count, PLAYLIST_PAGE_SIZE + 2)
        self.assertContains(first_page, videos[0].title)
        self.assertContains(first_page, videos[PLAYLIST_PAGE_SIZE - 1].title)
        self.assertNotContains(first_page, videos[PLAYLIST_PAGE_SIZE].title)
        self.assertContains(first_page, "?page=2")
        self.assertEqual(len(second_page.context["visible_items"]), 2)
        self.assertContains(second_page, videos[PLAYLIST_PAGE_SIZE].title)
        self.assertContains(second_page, videos[-1].title)
        self.assertContains(second_page, "?page=1")

    def test_inaccessible_items_do_not_count_toward_playlist_pages(self):
        playlist = Playlist.objects.create(
            owner=self.owner,
            name="Visibility-safe playlist",
            visibility=Playlist.Visibility.PUBLIC,
        )
        visible = self.make_video("Visible")
        hidden = self.make_video("Hidden", status=Video.PublicationStatus.DRAFT)
        PlaylistItem.objects.create(playlist=playlist, video=visible, position=0)
        PlaylistItem.objects.create(playlist=playlist, video=hidden, position=1)

        response = self.client.get(reverse("playlist_detail", args=[playlist.pk]))

        self.assertEqual(response.context["visible_items"].paginator.count, 1)
        self.assertContains(response, "Visible")
        self.assertNotContains(response, "Hidden")

    def test_invalid_playlist_page_falls_back_safely(self):
        playlist = Playlist.objects.create(
            owner=self.owner,
            name="Safe pages",
            visibility=Playlist.Visibility.PUBLIC,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video, position=0)

        response = self.client.get(reverse("playlist_detail", args=[playlist.pk]), {"page": "nope"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["visible_items"].number, 1)
