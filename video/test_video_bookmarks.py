from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Video, VideoBookmark
from .services.bookmarks import BookmarkValidationError, save_bookmark


class VideoBookmarkTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.video = Video.objects.create(
            title="Bookmark video",
            description="Video",
            thumbnail="videos/t.jpg",
            video_file="videos/v.mp4",
            author=self.owner,
        )

    def test_bookmark_routes_require_login_and_mutations_require_post(self):
        list_url = reverse("video_bookmark_list")
        create_url = reverse("video_bookmark_create", args=[self.video.pk])
        self.assertRedirects(self.client.get(list_url), f"/accounts/login/?next={list_url}")
        self.assertRedirects(self.client.post(create_url), f"/accounts/login/?next={create_url}")
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(create_url).status_code, 405)

    def test_viewer_can_save_and_relabel_the_same_moment(self):
        self.client.force_login(self.viewer)
        url = reverse("video_bookmark_create", args=[self.video.pk])
        self.assertRedirects(
            self.client.post(url, {"position_seconds": "62.4", "label": " First idea "}),
            reverse("video_detail", args=[self.video.pk]),
        )
        bookmark = VideoBookmark.objects.get()
        self.assertEqual((bookmark.position_seconds, bookmark.label), (62, "First idea"))
        self.client.post(url, {"position_seconds": "62", "label": "Updated idea"})
        self.assertEqual(VideoBookmark.objects.count(), 1)
        self.assertEqual(VideoBookmark.objects.get().label, "Updated idea")

    def test_service_rejects_invalid_labels_and_positions(self):
        invalid_values = [
            ("", 10),
            ("x" * 121, 10),
            ("Label", -1),
            ("Label", 86401),
            ("Label", "nan"),
            ("Label", "not-a-number"),
        ]
        for label, position in invalid_values:
            with self.subTest(label=label[:10], position=position), self.assertRaises(BookmarkValidationError):
                save_bookmark(user=self.viewer, video=self.video, position=position, label=label)
        self.assertFalse(VideoBookmark.objects.exists())

    def test_viewer_cannot_bookmark_an_inaccessible_video(self):
        self.video.publication_status = Video.PublicationStatus.DRAFT
        self.video.save(update_fields=["publication_status"])
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("video_bookmark_create", args=[self.video.pk]),
            {"position_seconds": 5, "label": "Forged"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(VideoBookmark.objects.exists())

    def test_video_page_lists_only_current_viewers_bookmarks_in_time_order(self):
        VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=90, label="Later")
        VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=5, label="Sooner")
        VideoBookmark.objects.create(user=self.other, video=self.video, position_seconds=1, label="Private note")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("video_detail", args=[self.video.pk]))
        self.assertContains(response, 'data-seek-time="5"')
        self.assertContains(response, "0:05 · Sooner")
        self.assertNotContains(response, "Private note")
        self.assertLess(response.content.index(b"Sooner"), response.content.index(b"Later"))
        self.assertContains(response, 'id="bookmark-position"')
        self.assertContains(response, "player.currentTime")

    def test_private_list_contains_only_owned_accessible_bookmarks(self):
        own = VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=5, label="Mine")
        VideoBookmark.objects.create(user=self.other, video=self.video, position_seconds=10, label="Not mine")
        hidden = Video.objects.create(
            title="Hidden",
            description="Draft",
            thumbnail="videos/h.jpg",
            video_file="videos/h.mp4",
            author=self.owner,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        VideoBookmark.objects.create(user=self.viewer, video=hidden, position_seconds=2, label="No longer visible")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("video_bookmark_list"))
        self.assertContains(response, own.label)
        self.assertNotContains(response, "Not mine")
        self.assertNotContains(response, "No longer visible")

    def test_removal_is_post_only_and_owner_scoped(self):
        bookmark = VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=5, label="Mine")
        url = reverse("video_bookmark_delete", args=[bookmark.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(VideoBookmark.objects.filter(pk=bookmark.pk).exists())
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("video_detail", args=[self.video.pk]))
        self.assertFalse(VideoBookmark.objects.exists())

    def test_bookmarks_cascade_when_video_is_permanently_deleted(self):
        VideoBookmark.objects.create(user=self.viewer, video=self.video, position_seconds=5, label="Mine")
        self.video.delete()
        self.assertFalse(VideoBookmark.objects.exists())
