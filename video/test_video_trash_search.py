from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Channel, Video
from .services.trash import TRASH_RETENTION


class VideoTrashSearchTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="trash-search-owner", password="password123")
        self.other = User.objects.create_user(username="trash-search-other", password="password123")
        self.channel = Channel.objects.create(owner=self.owner, name="Road Trips", description="Travel")
        self.other_channel = Channel.objects.create(owner=self.owner, name="Garage Projects", description="Builds")
        self.category = Category.objects.create(name="Travel", description="Travel", thumbnail="categories/travel.jpg")
        self.other_category = Category.objects.create(name="DIY", description="DIY", thumbnail="categories/diy.jpg")
        self.title_match = self.create_trashed_video("Alabama Campground Tour", "Quiet overnight stop", channel=self.channel, category=self.category)
        self.description_match = self.create_trashed_video("Battery Upgrade", "Lithium battery bank install", channel=self.other_channel, category=self.other_category)
        self.channel_match = self.create_trashed_video("Packing Day", "Getting ready", channel=self.channel, category=self.other_category)
        self.category_match = self.create_trashed_video("Camp Setup", "Weekend setup", channel=self.other_channel, category=self.category)
        self.foreign = self.create_trashed_video("Foreign Alabama Trash", "Should never appear", author=self.other)
        self.client.force_login(self.owner)

    def create_trashed_video(self, title, description, *, channel=None, category=None, author=None, age_days=1):
        video = Video.objects.create(
            title=title,
            description=description,
            thumbnail=f"videos/{title}.jpg",
            video_file=f"videos/{title}.mp4",
            author=author or self.owner,
            channel=channel,
            category=category,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        Video.objects.filter(pk=video.pk).update(deleted_at=timezone.now() - timedelta(days=age_days))
        video.refresh_from_db()
        return video

    def test_search_matches_title(self):
        response = self.client.get(reverse("creator_video_trash"), {"query": "alabama"})
        self.assertContains(response, self.title_match.title)
        self.assertNotContains(response, self.foreign.title)

    def test_search_matches_description(self):
        response = self.client.get(reverse("creator_video_trash"), {"query": "LITHIUM BATTERY"})
        self.assertContains(response, self.description_match.title)
        self.assertNotContains(response, self.title_match.title)

    def test_search_matches_channel_name(self):
        response = self.client.get(reverse("creator_video_trash"), {"query": "road trips"})
        self.assertContains(response, self.title_match.title)
        self.assertContains(response, self.channel_match.title)
        self.assertNotContains(response, self.description_match.title)

    def test_search_matches_category_name(self):
        response = self.client.get(reverse("creator_video_trash"), {"query": "travel"})
        self.assertContains(response, self.title_match.title)
        self.assertContains(response, self.category_match.title)
        self.assertNotContains(response, self.description_match.title)

    def test_search_applies_before_pagination(self):
        for index in range(30):
            self.create_trashed_video(f"Needle trash {index:02d}", "Search marker")

        response = self.client.get(reverse("creator_video_trash"), {"query": "needle"})

        self.assertEqual(len(response.context["videos"]), 25)
        self.assertEqual(response.context["videos"].paginator.count, 30)
        self.assertContains(response, "Page 1 of 2")
        self.assertContains(response, "query=needle&amp;page=2")

    def test_search_input_is_trimmed_and_blank_is_unfiltered(self):
        trimmed = self.client.get(reverse("creator_video_trash"), {"query": "  alabama  "})
        self.assertEqual(trimmed.context["selected_query"], "alabama")
        self.assertContains(trimmed, self.title_match.title)

        blank = self.client.get(reverse("creator_video_trash"), {"query": "   "})
        self.assertEqual(blank.context["selected_query"], "")
        self.assertContains(blank, self.title_match.title)
        self.assertContains(blank, self.description_match.title)

    def test_search_form_resets_page(self):
        response = self.client.get(reverse("creator_video_trash"), {"query": "travel", "page": 4})
        self.assertContains(response, 'name="query" value="travel"', html=False)
        self.assertNotContains(response, 'name="page"', html=False)

    def test_permanent_delete_preserves_query_and_page(self):
        video = self.create_trashed_video(
            "Delete searched trash",
            "needle",
            age_days=TRASH_RETENTION.days,
        )
        target = reverse("creator_video_trash") + "?query=needle&page=2"

        confirm = self.client.get(reverse("video_permanent_delete", args=[video.pk]), {"next": target})
        self.assertEqual(confirm.context["return_to"], target)

        response = self.client.post(reverse("video_permanent_delete", args=[video.pk]), {"next": target})
        self.assertRedirects(response, target, fetch_redirect_response=False)
        self.assertFalse(Video.objects.filter(pk=video.pk).exists())
