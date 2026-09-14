from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Playlist, PlaylistItem, Video


class PlaylistReorderingTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.category = Category.objects.create(name="General")
        self.playlist = Playlist.objects.create(
            owner=self.owner,
            name="Ordered playlist",
            visibility=Playlist.Visibility.PUBLIC,
        )
        self.items = []
        for index in range(3):
            video = Video.objects.create(
                title=f"Video {index}",
                description="Playlist ordering test",
                thumbnail=f"videos/thumbnails/{index}.jpg",
                video_file=f"videos/files/{index}.mp4",
                author=self.owner,
                category=self.category,
            )
            self.items.append(
                PlaylistItem.objects.create(
                    playlist=self.playlist,
                    video=video,
                    position=index,
                )
            )

    def reorder_url(self, item, direction):
        return reverse(
            "playlist_reorder_item",
            kwargs={
                "pk": self.playlist.pk,
                "item_pk": item.pk,
                "direction": direction,
            },
        )

    def ordered_item_ids(self):
        return list(
            self.playlist.items.order_by("position", "added_at", "pk").values_list(
                "pk", flat=True
            )
        )

    def test_owner_can_move_item_up(self):
        self.client.login(username="owner", password="password123")
        response = self.client.post(self.reorder_url(self.items[1], "up"))

        self.assertRedirects(response, reverse("playlist_detail", args=[self.playlist.pk]))
        self.assertEqual(
            self.ordered_item_ids(),
            [self.items[1].pk, self.items[0].pk, self.items[2].pk],
        )
        self.assertEqual(
            list(self.playlist.items.order_by("position").values_list("position", flat=True)),
            [0, 1, 2],
        )

    def test_owner_can_move_item_down(self):
        self.client.login(username="owner", password="password123")
        self.client.post(self.reorder_url(self.items[1], "down"))
        self.assertEqual(
            self.ordered_item_ids(),
            [self.items[0].pk, self.items[2].pk, self.items[1].pk],
        )

    def test_boundary_moves_are_no_ops(self):
        self.client.login(username="owner", password="password123")
        expected = self.ordered_item_ids()
        self.client.post(self.reorder_url(self.items[0], "up"))
        self.client.post(self.reorder_url(self.items[-1], "down"))
        self.assertEqual(self.ordered_item_ids(), expected)

    def test_non_owner_cannot_reorder(self):
        self.client.login(username="other", password="password123")
        response = self.client.post(self.reorder_url(self.items[1], "up"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.ordered_item_ids(), [item.pk for item in self.items])

    def test_reorder_requires_post_and_login(self):
        url = self.reorder_url(self.items[1], "up")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.client.login(username="owner", password="password123")
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_invalid_direction_does_not_change_order(self):
        self.client.login(username="owner", password="password123")
        with self.assertRaises(ValueError):
            self.client.post(self.reorder_url(self.items[1], "sideways"))
        self.assertEqual(self.ordered_item_ids(), [item.pk for item in self.items])

    def test_current_page_is_preserved(self):
        self.client.login(username="owner", password="password123")
        response = self.client.post(
            self.reorder_url(self.items[1], "up"),
            {"page": "2"},
        )
        self.assertRedirects(
            response,
            f"{reverse('playlist_detail', args=[self.playlist.pk])}?page=2",
        )

    def test_move_controls_are_owner_only(self):
        detail_url = reverse("playlist_detail", args=[self.playlist.pk])
        self.client.login(username="owner", password="password123")
        owner_response = self.client.get(detail_url)
        self.assertContains(owner_response, "Move up")
        self.assertContains(owner_response, "Move down")

        self.client.login(username="other", password="password123")
        other_response = self.client.get(detail_url)
        self.assertNotContains(other_response, "Move up")
        self.assertNotContains(other_response, "Move down")
