from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel


class ViewerCreatorExperienceTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.channel = Channel.objects.create(
            name="Creator channel",
            description="A creator channel",
            thumbnail=SimpleUploadedFile("channel.gif", self._gif(), content_type="image/gif"),
            owner=self.creator,
        )

    @staticmethod
    def _gif():
        return (
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        )

    def test_viewer_navigation_hides_creator_studio(self):
        self.client.login(username="viewer", password="password123")
        response = self.client.get(reverse("video_list"))

        self.assertContains(response, "Become a creator")
        self.assertNotContains(response, "Creator studio")
        self.assertNotContains(response, ">Upload</span>")

    def test_creator_navigation_shows_creator_studio(self):
        self.client.login(username="creator", password="password123")
        response = self.client.get(reverse("video_list"))

        self.assertContains(response, "Creator studio")
        self.assertContains(response, "My videos")
        self.assertContains(response, "Upload")

    def test_viewer_profile_identifies_viewer_account(self):
        self.client.login(username="viewer", password="password123")
        response = self.client.get(
            reverse("user_profile", kwargs={"username": self.viewer.username})
        )

        self.assertContains(response, "Viewer profile")
        self.assertContains(response, "Viewer — watch, subscribe, comment")

    def test_viewer_cannot_create_category(self):
        self.client.login(username="viewer", password="password123")
        response = self.client.get(reverse("category_create"))

        self.assertEqual(response.status_code, 403)

    def test_creator_can_create_category(self):
        self.client.login(username="creator", password="password123")
        response = self.client.post(
            reverse("category_create"),
            {
                "name": "Technology",
                "description": "Technology videos",
                "thumbnail": SimpleUploadedFile(
                    "category.gif", self._gif(), content_type="image/gif"
                ),
            },
        )

        category = Category.objects.get(name="Technology")
        self.assertRedirects(
            response, reverse("category_detail", kwargs={"pk": category.pk})
        )
