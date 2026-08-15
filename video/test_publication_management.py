from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Video


class PublicationManagementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner", password="password123"
        )
        self.other = User.objects.create_user(
            username="other", password="password123"
        )
        self.category = Category.objects.create(
            name="General",
            description="General",
            thumbnail="categories/general.jpg",
        )
        self.draft = self.create_video(
            "Draft video", self.owner, Video.PublicationStatus.DRAFT
        )
        self.unlisted = self.create_video(
            "Unlisted video", self.owner, Video.PublicationStatus.UNLISTED
        )
        self.scheduled = self.create_video(
            "Scheduled video",
            self.owner,
            Video.PublicationStatus.SCHEDULED,
            publish_at=timezone.now() + timedelta(days=1),
        )
        self.published = self.create_video(
            "Published video", self.owner, Video.PublicationStatus.PUBLISHED
        )
        self.foreign = self.create_video(
            "Foreign video", self.other, Video.PublicationStatus.DRAFT
        )

    def create_video(self, title, author, status, publish_at=None):
        return Video.objects.create(
            title=title,
            description=title,
            thumbnail=f"videos/{title}.jpg",
            video_file=f"videos/{title}.mp4",
            author=author,
            category=self.category,
            publication_status=status,
            publish_at=publish_at,
        )

    def test_library_requires_login(self):
        response = self.client.get(reverse("creator_video_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_library_contains_only_owned_videos(self):
        self.client.login(username="owner", password="password123")
        response = self.client.get(reverse("creator_video_list"))
        self.assertContains(response, self.draft.title)
        self.assertContains(response, self.unlisted.title)
        self.assertContains(response, self.scheduled.title)
        self.assertContains(response, self.published.title)
        self.assertNotContains(response, self.foreign.title)

    def test_each_publication_status_can_be_filtered(self):
        self.client.login(username="owner", password="password123")
        for status, expected in (
            (Video.PublicationStatus.DRAFT, self.draft),
            (Video.PublicationStatus.UNLISTED, self.unlisted),
            (Video.PublicationStatus.SCHEDULED, self.scheduled),
            (Video.PublicationStatus.PUBLISHED, self.published),
        ):
            with self.subTest(status=status):
                response = self.client.get(
                    reverse("creator_video_list"), {"status": status}
                )
                self.assertEqual(list(response.context["videos"]), [expected])
                self.assertEqual(response.context["selected_status"], status)

    def test_invalid_filter_safely_falls_back_to_all(self):
        self.client.login(username="owner", password="password123")
        response = self.client.get(
            reverse("creator_video_list"), {"status": "private"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected_status"], "all")
        self.assertEqual(len(response.context["videos"]), 4)

    def test_bulk_action_requires_post(self):
        self.client.login(username="owner", password="password123")
        response = self.client.get(reverse("creator_video_bulk_publication"))
        self.assertEqual(response.status_code, 405)

    def test_bulk_action_updates_selected_owned_videos_and_clears_publish_time(self):
        self.client.login(username="owner", password="password123")
        response = self.client.post(
            reverse("creator_video_bulk_publication"),
            {
                "video_ids": [self.scheduled.pk, self.published.pk],
                "publication_status": Video.PublicationStatus.UNLISTED,
            },
        )
        self.assertRedirects(response, reverse("creator_video_list"))
        self.scheduled.refresh_from_db()
        self.published.refresh_from_db()
        self.draft.refresh_from_db()
        self.assertEqual(
            self.scheduled.publication_status, Video.PublicationStatus.UNLISTED
        )
        self.assertIsNone(self.scheduled.publish_at)
        self.assertEqual(
            self.published.publication_status, Video.PublicationStatus.UNLISTED
        )
        self.assertEqual(self.draft.publication_status, Video.PublicationStatus.DRAFT)

    def test_forged_foreign_id_is_not_updated(self):
        self.client.login(username="owner", password="password123")
        self.client.post(
            reverse("creator_video_bulk_publication"),
            {
                "video_ids": [self.draft.pk, self.foreign.pk],
                "publication_status": Video.PublicationStatus.PUBLISHED,
            },
        )
        self.draft.refresh_from_db()
        self.foreign.refresh_from_db()
        self.assertEqual(
            self.draft.publication_status, Video.PublicationStatus.PUBLISHED
        )
        self.assertEqual(
            self.foreign.publication_status, Video.PublicationStatus.DRAFT
        )

    def test_invalid_action_and_selection_do_not_mutate_videos(self):
        self.client.login(username="owner", password="password123")
        url = reverse("creator_video_bulk_publication")
        invalid_status = self.client.post(
            url,
            {
                "video_ids": [self.draft.pk],
                "publication_status": Video.PublicationStatus.SCHEDULED,
            },
        )
        invalid_id = self.client.post(
            url,
            {
                "video_ids": ["not-an-id"],
                "publication_status": Video.PublicationStatus.PUBLISHED,
            },
        )
        self.assertEqual(invalid_status.status_code, 400)
        self.assertEqual(invalid_id.status_code, 400)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.publication_status, Video.PublicationStatus.DRAFT)

    def test_empty_selection_is_safe(self):
        self.client.login(username="owner", password="password123")
        response = self.client.post(
            reverse("creator_video_bulk_publication"),
            {"publication_status": Video.PublicationStatus.DRAFT},
        )
        self.assertRedirects(response, reverse("creator_video_list"))
        self.published.refresh_from_db()
        self.assertEqual(
            self.published.publication_status, Video.PublicationStatus.PUBLISHED
        )

    def test_empty_filtered_library_has_useful_message(self):
        Video.objects.filter(author=self.owner).delete()
        self.client.login(username="owner", password="password123")
        response = self.client.get(
            reverse("creator_video_list"), {"status": Video.PublicationStatus.DRAFT}
        )
        self.assertContains(response, "No videos match this publication status.")

    def test_authenticated_navigation_links_to_library(self):
        self.client.login(username="owner", password="password123")
        response = self.client.get(reverse("video_list"))
        self.assertContains(response, reverse("creator_video_list"))
