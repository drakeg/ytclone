from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Channel, Video


class CreatorVideoSearchTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="video-search-creator",
            password="password123",
        )
        self.other = User.objects.create_user(
            username="video-search-other",
            password="password123",
        )
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Road Trips",
            description="Travel channel",
        )
        self.other_channel = Channel.objects.create(
            owner=self.creator,
            name="Garage Projects",
            description="Builds channel",
        )
        self.category = Category.objects.create(
            name="Travel",
            description="Travel category",
            thumbnail="categories/travel.jpg",
        )
        self.other_category = Category.objects.create(
            name="DIY",
            description="DIY category",
            thumbnail="categories/diy.jpg",
        )
        self.title_match = self.create_video(
            "Alabama Campground Tour",
            "A quiet overnight stop.",
            channel=self.channel,
            category=self.category,
        )
        self.description_match = self.create_video(
            "Battery Upgrade",
            "Installing a lithium battery bank in the fifth wheel.",
            channel=self.other_channel,
            category=self.other_category,
        )
        self.channel_match = self.create_video(
            "Packing Day",
            "Getting ready to leave.",
            channel=self.channel,
            category=self.other_category,
        )
        self.category_match = self.create_video(
            "Camp Setup",
            "Setting up for the weekend.",
            channel=self.other_channel,
            category=self.category,
            status=Video.PublicationStatus.DRAFT,
        )
        self.foreign = self.create_video(
            "Foreign Alabama Video",
            "Should never appear.",
            author=self.other,
        )
        self.trashed = self.create_video(
            "Trashed Alabama Video",
            "Should never appear.",
        )
        self.trashed.deleted_at = timezone.now()
        self.trashed.save(update_fields=["deleted_at"])
        self.client.force_login(self.creator)

    def create_video(
        self,
        title,
        description,
        *,
        channel=None,
        category=None,
        status=Video.PublicationStatus.PUBLISHED,
        author=None,
    ):
        return Video.objects.create(
            title=title,
            description=description,
            thumbnail=f"videos/{title}.jpg",
            video_file=f"videos/{title}.mp4",
            author=author or self.creator,
            channel=channel,
            category=category,
            publication_status=status,
        )

    def test_search_matches_title_case_insensitively(self):
        response = self.client.get(
            reverse("creator_video_list"),
            {"query": "alabama"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.title_match.title)
        self.assertNotContains(response, self.foreign.title)
        self.assertNotContains(response, self.trashed.title)

    def test_search_matches_description_case_insensitively(self):
        response = self.client.get(
            reverse("creator_video_list"),
            {"query": "LITHIUM BATTERY"},
        )

        self.assertContains(response, self.description_match.title)
        self.assertNotContains(response, self.title_match.title)

    def test_search_matches_channel_name_case_insensitively(self):
        response = self.client.get(
            reverse("creator_video_list"),
            {"query": "road trips"},
        )

        self.assertContains(response, self.title_match.title)
        self.assertContains(response, self.channel_match.title)
        self.assertNotContains(response, self.description_match.title)

    def test_search_matches_category_name_case_insensitively(self):
        response = self.client.get(
            reverse("creator_video_list"),
            {"query": "travel"},
        )

        self.assertContains(response, self.title_match.title)
        self.assertContains(response, self.category_match.title)
        self.assertNotContains(response, self.description_match.title)

    def test_search_combines_with_status_before_pagination(self):
        for index in range(30):
            self.create_video(
                f"Needle published {index:02d}",
                "Search marker",
                status=Video.PublicationStatus.PUBLISHED,
            )
        for index in range(30):
            self.create_video(
                f"Needle draft {index:02d}",
                "Search marker",
                status=Video.PublicationStatus.DRAFT,
            )

        response = self.client.get(
            reverse("creator_video_list"),
            {
                "status": Video.PublicationStatus.DRAFT,
                "query": "needle",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 25)
        self.assertEqual(response.context["videos"].paginator.count, 30)
        self.assertContains(response, "Page 1 of 2")
        self.assertNotContains(response, "Needle published")
        self.assertContains(
            response,
            f"status={Video.PublicationStatus.DRAFT}&amp;query=needle&amp;page=2",
        )

    def test_search_input_is_trimmed_and_blank_is_unfiltered(self):
        trimmed = self.client.get(
            reverse("creator_video_list"),
            {"query": "  alabama  "},
        )
        self.assertEqual(trimmed.context["selected_query"], "alabama")
        self.assertContains(trimmed, self.title_match.title)

        blank = self.client.get(
            reverse("creator_video_list"),
            {"query": "   "},
        )
        self.assertEqual(blank.context["selected_query"], "")
        self.assertContains(blank, self.title_match.title)
        self.assertContains(blank, self.description_match.title)

    def test_status_links_preserve_search_and_reset_page(self):
        response = self.client.get(
            reverse("creator_video_list"),
            {
                "status": Video.PublicationStatus.DRAFT,
                "query": "travel",
                "page": 4,
            },
        )

        base = reverse("creator_video_list")
        self.assertContains(
            response,
            f'href="{base}?status=all&amp;query=travel"',
            html=False,
        )
        self.assertContains(
            response,
            f'href="{base}?status={Video.PublicationStatus.PUBLISHED}&amp;query=travel"',
            html=False,
        )

    def test_search_form_preserves_status_and_resets_page(self):
        response = self.client.get(
            reverse("creator_video_list"),
            {
                "status": Video.PublicationStatus.DRAFT,
                "query": "travel",
                "page": 4,
            },
        )

        self.assertContains(
            response,
            f'name="status" value="{Video.PublicationStatus.DRAFT}"',
            html=False,
        )
        self.assertContains(
            response,
            'name="query" value="travel"',
            html=False,
        )
        self.assertNotContains(response, 'name="page"', html=False)

    def test_bulk_action_returns_to_same_search_status_and_page(self):
        target = (
            reverse("creator_video_list")
            + f"?status={Video.PublicationStatus.PUBLISHED}&query=alabama&page=2"
        )

        response = self.client.post(
            reverse("creator_video_bulk_publication"),
            {
                "video_ids": [self.title_match.pk],
                "publication_status": Video.PublicationStatus.DRAFT,
                "next": target,
            },
        )

        self.assertRedirects(response, target, fetch_redirect_response=False)
        self.title_match.refresh_from_db()
        self.assertEqual(
            self.title_match.publication_status,
            Video.PublicationStatus.DRAFT,
        )
