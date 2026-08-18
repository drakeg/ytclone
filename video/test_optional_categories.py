from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .forms import VideoUploadForm
from .models import Category, Channel, Video


class OptionalVideoCategoryTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            username="viewer", password="password123"
        )
        self.creator = User.objects.create_user(
            username="creator", password="password123"
        )
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Creator Channel",
            description="Creator uploads",
        )

    def test_upload_form_category_is_optional_with_zero_categories(self):
        form = VideoUploadForm(user=self.creator)

        self.assertFalse(form.fields["category"].required)
        self.assertEqual(form.fields["category"].queryset.count(), 0)

    def test_upload_page_offers_inline_category_creation(self):
        self.client.login(username="creator", password="password123")

        response = self.client.get(reverse("upload"))

        self.assertContains(response, "Category is optional")
        self.assertContains(response, 'id="inline-category-name"')
        self.assertContains(response, reverse("category_create_inline"))

    def test_creator_can_create_category_inline_without_artwork(self):
        self.client.login(username="creator", password="password123")

        response = self.client.post(
            reverse("category_create_inline"), {"name": "Travel"}
        )

        self.assertEqual(response.status_code, 201)
        category = Category.objects.get(name="Travel")
        self.assertEqual(response.json()["id"], category.pk)
        self.assertTrue(response.json()["created"])
        self.assertEqual(category.description, "")
        self.assertFalse(bool(category.thumbnail))

    def test_inline_category_creation_reuses_case_insensitive_match(self):
        existing = Category.objects.create(name="Travel")
        self.client.login(username="creator", password="password123")

        response = self.client.post(
            reverse("category_create_inline"), {"name": "travel"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], existing.pk)
        self.assertFalse(response.json()["created"])
        self.assertEqual(Category.objects.count(), 1)

    def test_viewer_cannot_create_category_inline(self):
        self.client.login(username="viewer", password="password123")

        response = self.client.post(
            reverse("category_create_inline"), {"name": "Travel"}
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Category.objects.exists())

    def test_deleting_category_does_not_delete_video(self):
        category = Category.objects.create(name="Travel")
        video = Video.objects.create(
            title="Trip",
            description="A trip",
            thumbnail="videos/thumbnails/trip.jpg",
            video_file="videos/files/trip.mp4",
            author=self.creator,
            channel=self.channel,
            category=category,
        )

        category.delete()

        video.refresh_from_db()
        self.assertIsNone(video.category)
