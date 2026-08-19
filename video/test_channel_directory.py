from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video


class ChannelDirectoryTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="creator", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.channel = Channel.objects.create(
            owner=self.owner,
            name="Creator Channel",
            description="A channel with useful videos and a growing community.",
        )
        self.channel.subscribers.add(self.viewer)

    def _video(self, title, *, status=Video.PublicationStatus.PUBLISHED, audience=Video.Audience.EVERYONE):
        return Video.objects.create(
            title=title,
            description="Description",
            thumbnail=SimpleUploadedFile("thumb.jpg", b"image", content_type="image/jpeg"),
            video_file=SimpleUploadedFile("video.mp4", b"video", content_type="video/mp4"),
            author=self.owner,
            channel=self.channel,
            publication_status=status,
            audience=audience,
        )

    def test_directory_renders_channel_identity_and_stats(self):
        self._video("Public video")
        self._video("Draft video", status=Video.PublicationStatus.DRAFT)
        self._video("Members video", audience=Video.Audience.MEMBERS_ONLY)

        response = self.client.get(reverse("channel_list"))

        self.assertContains(response, "Creator Channel")
        self.assertContains(response, "@creator")
        self.assertContains(response, "1 subscriber")
        self.assertContains(response, "1 public video")
        self.assertContains(response, reverse("channel_detail", args=[self.channel.pk]))
        self.assertContains(response, reverse("user_profile", args=[self.owner.username]))

    def test_channel_without_thumbnail_uses_letter_avatar_in_directory(self):
        response = self.client.get(reverse("channel_list"))
        body = response.content.decode()

        self.assertContains(response, "Creator Channel default channel avatar")
        self.assertIn("C", body)
        self.assertContains(response, "border-radius: 50%")

    def test_channel_without_thumbnail_uses_letter_avatar_on_channel_page(self):
        response = self.client.get(reverse("channel_detail", args=[self.channel.pk]))

        self.assertContains(response, "Creator Channel default channel avatar")
        self.assertContains(response, "font-weight: 850")
        self.assertContains(response, "border-radius: 50%")

    def test_uploaded_thumbnail_replaces_default_letter_avatar(self):
        self.channel.thumbnail = SimpleUploadedFile(
            "channel.jpg", b"image", content_type="image/jpeg"
        )
        self.channel.save(update_fields=["thumbnail"])

        response = self.client.get(reverse("channel_detail", args=[self.channel.pk]))

        self.assertContains(response, "channel.jpg")
        self.assertNotContains(response, "default channel avatar")

    def test_owner_sees_creator_actions_for_own_channel(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("channel_list"))

        self.assertContains(response, "Your channel")
        self.assertContains(response, reverse("monetization:creator_dashboard", args=[self.channel.pk]))

    def test_empty_directory_has_useful_empty_state(self):
        Channel.objects.all().delete()
        response = self.client.get(reverse("channel_list"))

        self.assertContains(response, "No channels yet")
        self.assertNotContains(response, "View channel")
