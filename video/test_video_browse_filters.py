from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Channel, Video
from .services.video_browse import browse_videos


class VideoBrowseFilterTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="browse-filter-creator", password="password123")
        self.viewer = User.objects.create_user(username="browse-filter-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Browse Filter Channel", description="Browse")
        self.travel = Category.objects.create(name="Travel", description="Travel videos")
        self.food = Category.objects.create(name="Food", description="Food videos")

    def video(self, title, *, category=None, views=0, audience=Video.Audience.EVERYONE):
        return Video.objects.create(
            title=title,
            description=title,
            thumbnail=f"videos/thumbnails/{title}.jpg",
            video_file=f"videos/files/{title}.mp4",
            author=self.creator,
            channel=self.channel,
            category=category,
            views=views,
            audience=audience,
        )

    def test_category_filter_only_returns_selected_category(self):
        travel = self.video("travel", category=self.travel)
        self.video("food", category=self.food)
        self.video("uncategorized")

        videos, selected_sort = browse_videos(self.viewer, category=self.travel.pk)

        self.assertEqual(selected_sort, "newest")
        self.assertEqual(list(videos), [travel])

    def test_invalid_category_falls_back_to_all_categories(self):
        first = self.video("first", category=self.travel)
        second = self.video("second", category=self.food)

        videos, _selected_sort = browse_videos(self.viewer, category="not-a-category")

        self.assertEqual(list(videos), [second, first])

    def test_all_upload_date_filters_exclude_old_uploads(self):
        old = self.video("old", category=self.travel)
        recent = self.video("recent", category=self.travel)
        Video.objects.filter(pk=old.pk).update(pub_date=timezone.now() - timedelta(days=400))

        for uploaded in ("today", "week", "month", "year"):
            with self.subTest(uploaded=uploaded):
                videos, _selected_sort = browse_videos(self.viewer, uploaded=uploaded)
                self.assertIn(recent, list(videos))
                self.assertNotIn(old, list(videos))

    def test_invalid_upload_filter_falls_back_to_any_time(self):
        old = self.video("old", category=self.travel)
        Video.objects.filter(pk=old.pk).update(pub_date=timezone.now() - timedelta(days=400))

        videos, _selected_sort = browse_videos(self.viewer, uploaded="forever")

        self.assertEqual(list(videos), [old])

    def test_filters_combine_with_existing_sort(self):
        lower = self.video("lower", category=self.travel, views=10)
        higher = self.video("higher", category=self.travel, views=50)
        self.video("food-popular", category=self.food, views=500)

        videos, selected_sort = browse_videos(
            self.viewer,
            sort="views",
            category=self.travel.pk,
            uploaded="year",
        )

        self.assertEqual(selected_sort, "views")
        self.assertEqual(list(videos), [higher, lower])

    def test_filters_keep_central_visibility_rules(self):
        public = self.video("public", category=self.travel)
        self.video("members", category=self.travel, audience=Video.Audience.MEMBERS_ONLY)

        videos, _selected_sort = browse_videos(self.viewer, category=self.travel.pk)

        self.assertEqual(list(videos), [public])

    def test_page_renders_selected_filters_and_preserves_them_in_pagination(self):
        for number in range(25):
            self.video(f"travel-{number}", category=self.travel)
        self.video("food", category=self.food)

        response = self.client.get(
            reverse("video_browse"),
            {"sort": "views", "category": self.travel.pk, "uploaded": "year"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 24)
        self.assertEqual(response.context["selected_category"], self.travel)
        self.assertEqual(response.context["selected_upload"], "year")
        self.assertContains(response, f'value="{self.travel.pk}" selected')
        self.assertContains(response, 'value="year" selected')
        self.assertContains(response, f"category={self.travel.pk}")
        self.assertContains(response, "uploaded=year")
        self.assertContains(response, "page=2")

    def test_filter_form_does_not_preserve_page_number(self):
        response = self.client.get(
            reverse("video_browse"),
            {"sort": "newest", "category": self.travel.pk, "uploaded": "any", "page": 3},
        )

        self.assertNotContains(response, 'name="page"')
