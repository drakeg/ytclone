from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel


class UploadDragDropTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="creator", password="password123"
        )
        Channel.objects.create(
            owner=self.user,
            name="Creator Channel",
            description="Channel for uploads",
        )
        self.client.login(username="creator", password="password123")

    def test_upload_page_offers_drag_and_drop_fallback(self):
        response = self.client.get(reverse("upload"))

        self.assertContains(response, 'id="video-drop-zone"')
        self.assertContains(response, "Drag your video here")
        self.assertContains(response, "avoids opening Chrome's file picker")
        self.assertContains(response, "new DataTransfer()")
        self.assertContains(response, "document.getElementById('id_video_file')")
