from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Video
from .services.trash import TRASH_RETENTION


class VideoTrashPaginationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="trash-page-owner",
            password="password123",
        )
        self.other = User.objects.create_user(
            username="trash-page-other",
            password="password123",
        )
        self.client.force_login(self.owner)

    def create_trashed_video(self, title, *, author=None, age_days=1):
        video = Video.objects.create(
            title=title,
            description=title,
            thumbnail=f"videos/{title}.jpg",
            video_file=f"videos/{title}.mp4",
            author=author or self.owner,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        Video.objects.filter(pk=video.pk).update(
            deleted_at=timezone.now() - timedelta(days=age_days)
        )
        video.refresh_from_db()
        return video

    def test_trash_is_paginated_at_twenty_five(self):
        videos = [
            self.create_trashed_video(f"Trashed video {index:02d}")
            for index in range(1, 28)
        ]

        first = self.client.get(reverse("creator_video_trash"))

        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.context["videos"]), 25)
        self.assertContains(first, "Page 1 of 2")
        for video in videos[-25:]:
            self.assertContains(first, video.title)
        for video in videos[:2]:
            self.assertNotContains(first, video.title)

        second = self.client.get(
            reverse("creator_video_trash"),
            {"page": 2},
        )
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(second.context["videos"]), 2)
        for video in videos[:2]:
            self.assertContains(second, video.title)

    def test_foreign_trash_never_appears(self):
        own = self.create_trashed_video("Owned trash")
        foreign = self.create_trashed_video(
            "Foreign trash",
            author=self.other,
        )

        response = self.client.get(reverse("creator_video_trash"))

        self.assertContains(response, own.title)
        self.assertNotContains(response, foreign.title)

    def test_invalid_page_values_fall_back_safely(self):
        for index in range(27):
            self.create_trashed_video(f"Trash fallback {index:02d}")

        invalid = self.client.get(
            reverse("creator_video_trash"),
            {"page": "not-a-number"},
        )
        self.assertEqual(invalid.status_code, 200)
        self.assertEqual(invalid.context["videos"].number, 1)

        out_of_range = self.client.get(
            reverse("creator_video_trash"),
            {"page": 999},
        )
        self.assertEqual(out_of_range.status_code, 200)
        self.assertEqual(
            out_of_range.context["videos"].number,
            out_of_range.context["videos"].paginator.num_pages,
        )

    def test_permanent_delete_confirmation_preserves_trash_page(self):
        video = self.create_trashed_video(
            "Old enough to delete",
            age_days=TRASH_RETENTION.days,
        )
        target = reverse("creator_video_trash") + "?page=2"

        response = self.client.get(
            reverse("video_permanent_delete", args=[video.pk]),
            {"next": target},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["return_to"], target)
        self.assertContains(
            response,
            f'name="next" value="{target}"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{target}"',
            html=False,
        )

    def test_permanent_delete_returns_to_originating_trash_page(self):
        video = self.create_trashed_video(
            "Delete and return",
            age_days=TRASH_RETENTION.days,
        )
        target = reverse("creator_video_trash") + "?page=2"

        response = self.client.post(
            reverse("video_permanent_delete", args=[video.pk]),
            {"next": target},
        )

        self.assertRedirects(response, target, fetch_redirect_response=False)
        self.assertFalse(Video.objects.filter(pk=video.pk).exists())

    def test_permanent_delete_rejects_external_return_target(self):
        video = self.create_trashed_video(
            "Reject external return",
            age_days=TRASH_RETENTION.days,
        )

        response = self.client.post(
            reverse("video_permanent_delete", args=[video.pk]),
            {"next": "https://evil.example/phish"},
        )

        self.assertRedirects(
            response,
            reverse("creator_video_trash"),
            fetch_redirect_response=False,
        )
        self.assertFalse(Video.objects.filter(pk=video.pk).exists())

    def test_restore_behavior_remains_my_videos_draft(self):
        video = self.create_trashed_video("Restore still unchanged")

        response = self.client.post(
            reverse("video_restore", args=[video.pk]),
        )

        self.assertRedirects(
            response,
            reverse("creator_video_list"),
            fetch_redirect_response=False,
        )
        video.refresh_from_db()
        self.assertIsNone(video.deleted_at)
        self.assertEqual(video.publication_status, Video.PublicationStatus.DRAFT)
