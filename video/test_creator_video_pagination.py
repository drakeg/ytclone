from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Video


class CreatorVideoPaginationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="video-page-creator",
            password="password123",
        )
        self.other = User.objects.create_user(
            username="video-page-other",
            password="password123",
        )
        self.client.force_login(self.creator)

    def create_video(self, title, *, status=Video.PublicationStatus.PUBLISHED, author=None):
        return Video.objects.create(
            title=title,
            description=title,
            thumbnail=f"videos/{title}.jpg",
            video_file=f"videos/{title}.mp4",
            author=author or self.creator,
            publication_status=status,
        )

    def test_creator_library_is_paginated_at_twenty_five(self):
        videos = [
            self.create_video(f"Creator video {index:02d}")
            for index in range(1, 28)
        ]

        first_page = self.client.get(reverse("creator_video_list"))

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(len(first_page.context["videos"]), 25)
        self.assertContains(first_page, "Page 1 of 2")
        for video in videos[-25:]:
            self.assertContains(first_page, video.title)
        for video in videos[:2]:
            self.assertNotContains(first_page, video.title)

        second_page = self.client.get(
            reverse("creator_video_list"),
            {"page": 2},
        )
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(len(second_page.context["videos"]), 2)
        for video in videos[:2]:
            self.assertContains(second_page, video.title)

    def test_status_filter_is_applied_before_pagination(self):
        for index in range(26):
            self.create_video(
                f"Published video {index:02d}",
                status=Video.PublicationStatus.PUBLISHED,
            )
        drafts = [
            self.create_video(
                f"Draft video {index:02d}",
                status=Video.PublicationStatus.DRAFT,
            )
            for index in range(26)
        ]

        response = self.client.get(
            reverse("creator_video_list"),
            {"status": Video.PublicationStatus.DRAFT},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 25)
        self.assertEqual(response.context["videos"].paginator.count, 26)
        self.assertContains(response, "Page 1 of 2")
        self.assertNotContains(response, "Published video")
        self.assertContains(response, drafts[-1].title)
        self.assertContains(
            response,
            f"status={Video.PublicationStatus.DRAFT}&amp;page=2",
        )

    def test_status_filter_links_reset_pagination(self):
        response = self.client.get(
            reverse("creator_video_list"),
            {"status": Video.PublicationStatus.DRAFT, "page": 3},
        )

        base = reverse("creator_video_list")
        self.assertContains(
            response,
            f'href="{base}?status=all"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{base}?status={Video.PublicationStatus.PUBLISHED}"',
            html=False,
        )

    def test_bulk_action_preserves_current_filter_and_page(self):
        video = self.create_video(
            "Preserve library return",
            status=Video.PublicationStatus.PUBLISHED,
        )
        target = (
            reverse("creator_video_list")
            + f"?status={Video.PublicationStatus.PUBLISHED}&page=2"
        )

        response = self.client.post(
            reverse("creator_video_bulk_publication"),
            {
                "video_ids": [video.pk],
                "publication_status": Video.PublicationStatus.DRAFT,
                "next": target,
            },
        )

        self.assertRedirects(response, target, fetch_redirect_response=False)
        video.refresh_from_db()
        self.assertEqual(video.publication_status, Video.PublicationStatus.DRAFT)

    def test_bulk_action_rejects_external_return_target(self):
        video = self.create_video("Reject external library return")

        response = self.client.post(
            reverse("creator_video_bulk_publication"),
            {
                "video_ids": [video.pk],
                "publication_status": Video.PublicationStatus.DRAFT,
                "next": "https://evil.example/phish",
            },
        )

        self.assertRedirects(
            response,
            reverse("creator_video_list"),
            fetch_redirect_response=False,
        )

    def test_foreign_videos_never_appear_in_creator_pages(self):
        own = self.create_video("Owned paginated video")
        foreign = self.create_video(
            "Foreign paginated video",
            author=self.other,
        )

        response = self.client.get(reverse("creator_video_list"))

        self.assertContains(response, own.title)
        self.assertNotContains(response, foreign.title)

    def test_invalid_page_values_fall_back_safely(self):
        for index in range(27):
            self.create_video(f"Fallback creator video {index:02d}")

        invalid = self.client.get(
            reverse("creator_video_list"),
            {"page": "not-a-number"},
        )
        self.assertEqual(invalid.status_code, 200)
        self.assertEqual(invalid.context["videos"].number, 1)

        out_of_range = self.client.get(
            reverse("creator_video_list"),
            {"page": 999},
        )
        self.assertEqual(out_of_range.status_code, 200)
        self.assertEqual(
            out_of_range.context["videos"].number,
            out_of_range.context["videos"].paginator.num_pages,
        )
