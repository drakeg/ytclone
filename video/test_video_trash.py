from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Channel, Comment, Playlist, PlaylistItem, Video, WatchHistory
from .services.analytics import get_channel_analytics, get_creator_analytics
from .services.trash import TRASH_RETENTION


class VideoTrashTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", password="password123"
        )
        self.viewer = User.objects.create_user(
            username="viewer", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General",
            thumbnail="categories/general.jpg",
        )
        self.channel = Channel.objects.create(
            name="Channel",
            description="Channel",
            thumbnail="channels/channel.jpg",
            owner=self.owner,
        )
        self.video = Video.objects.create(
            title="Recoverable video",
            description="Recoverable",
            thumbnail="videos/recoverable.jpg",
            video_file="videos/recoverable.mp4",
            author=self.owner,
            channel=self.channel,
            category=self.category,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )

    def trash(self):
        self.client.login(username="owner", password="password123")
        return self.client.post(reverse("video_delete", kwargs={"pk": self.video.pk}))

    def test_trash_requires_owner_and_post_to_mutate(self):
        url = reverse("video_delete", kwargs={"pk": self.video.pk})
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.login(username="viewer", password="password123")
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.logout()
        self.client.login(username="owner", password="password123")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.video.refresh_from_db()
        self.assertIsNone(self.video.deleted_at)

    def test_trash_hides_video_and_resets_publication(self):
        response = self.trash()
        self.assertRedirects(response, reverse("creator_video_list"))
        self.video.refresh_from_db()
        self.assertIsNotNone(self.video.deleted_at)
        self.assertEqual(self.video.publication_status, Video.PublicationStatus.DRAFT)
        self.assertIsNone(self.video.publish_at)
        self.assertFalse(self.video.is_visible_to(self.owner))
        self.assertEqual(
            self.client.get(reverse("video_detail", kwargs={"pk": self.video.pk})).status_code,
            404,
        )

    def test_trashed_video_is_excluded_from_public_and_creator_surfaces(self):
        self.trash()
        self.client.logout()
        urls = [
            reverse("video_list"),
            reverse("search") + "?query=Recoverable",
            reverse("channel_detail", kwargs={"pk": self.channel.pk}),
            reverse("category_detail", kwargs={"pk": self.category.pk}),
            reverse("user_profile", kwargs={"username": self.owner.username}),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), self.video.title)
        self.client.login(username="owner", password="password123")
        self.assertNotContains(
            self.client.get(reverse("creator_video_list")), self.video.title
        )
        self.assertEqual(get_creator_analytics(self.owner).video_count, 0)
        self.assertEqual(get_channel_analytics(self.channel).video_count, 0)

    def test_mutation_routes_reject_trashed_video(self):
        self.trash()
        self.client.logout()
        self.client.login(username="viewer", password="password123")
        for name in ("playback_progress", "add_comment", "like_video", "dislike_video"):
            with self.subTest(name=name):
                response = self.client.post(
                    reverse(name, kwargs={"pk": self.video.pk}),
                    data={"comment": "Nope"},
                )
                self.assertEqual(response.status_code, 404)

    def test_trash_is_private_and_owner_scoped(self):
        self.trash()
        trash_url = reverse("creator_video_trash")
        self.client.logout()
        self.assertEqual(self.client.get(trash_url).status_code, 302)
        self.client.login(username="viewer", password="password123")
        self.assertNotContains(self.client.get(trash_url), self.video.title)
        self.assertEqual(
            self.client.post(reverse("video_restore", kwargs={"pk": self.video.pk})).status_code,
            404,
        )

    def test_restore_requires_post_and_returns_video_as_draft(self):
        self.trash()
        url = reverse("video_restore", kwargs={"pk": self.video.pk})
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)
        self.assertRedirects(response, reverse("creator_video_list"))
        self.video.refresh_from_db()
        self.assertIsNone(self.video.deleted_at)
        self.assertEqual(self.video.publication_status, Video.PublicationStatus.DRAFT)
        self.assertIsNone(self.video.publish_at)

    def test_related_records_remain_during_retention(self):
        Comment.objects.create(video=self.video, author=self.viewer, comment="Keep")
        WatchHistory.objects.create(video=self.video, user=self.viewer)
        playlist = Playlist.objects.create(owner=self.viewer, name="Keep")
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.video.likes.add(self.viewer)
        self.trash()
        self.assertTrue(Comment.objects.filter(video=self.video).exists())
        self.assertTrue(WatchHistory.objects.filter(video=self.video).exists())
        self.assertTrue(PlaylistItem.objects.filter(video=self.video).exists())
        self.assertTrue(self.video.likes.filter(pk=self.viewer.pk).exists())

    def test_permanent_delete_is_blocked_before_retention(self):
        self.trash()
        url = reverse("video_permanent_delete", kwargs={"pk": self.video.pk})
        response = self.client.get(url)
        self.assertContains(response, "remains protected until")
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Video.objects.filter(pk=self.video.pk).exists())

    def test_permanent_delete_after_retention_removes_database_records_but_not_media(self):
        Comment.objects.create(video=self.video, author=self.viewer, comment="Remove")
        self.trash()
        Video.objects.filter(pk=self.video.pk).update(
            deleted_at=timezone.now() - TRASH_RETENTION
        )
        self.video.refresh_from_db()
        url = reverse("video_permanent_delete", kwargs={"pk": self.video.pk})
        self.assertContains(self.client.get(url), "This action cannot be undone")
        with patch.object(self.video.video_file.storage, "delete") as storage_delete:
            response = self.client.post(url)
        storage_delete.assert_not_called()
        self.assertRedirects(response, reverse("creator_video_trash"))
        self.assertFalse(Video.objects.filter(pk=self.video.pk).exists())
        self.assertFalse(Comment.objects.exists())

    def test_retention_boundary_is_thirty_days(self):
        self.trash()
        self.video.refresh_from_db()
        expected = self.video.deleted_at + timedelta(days=30)
        response = self.client.get(
            reverse("video_permanent_delete", kwargs={"pk": self.video.pk})
        )
        self.assertEqual(response.context["available_at"], expected)

    def test_active_video_cannot_use_trash_only_routes(self):
        self.client.login(username="owner", password="password123")
        for name in ("video_restore", "video_permanent_delete"):
            with self.subTest(name=name):
                self.assertEqual(
                    self.client.post(reverse(name, kwargs={"pk": self.video.pk})).status_code,
                    404,
                )
