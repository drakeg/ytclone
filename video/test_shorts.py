from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse

from .forms import VideoEditForm, VideoUploadForm
from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsFoundationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.viewer = User.objects.create_user(username="viewer", password="password123")
        self.channel = Channel.objects.create(
            owner=self.creator,
            name="Shorts Test Channel",
            description="Channel for Shorts regression coverage",
        )
        self.video = Video.objects.create(
            title="Standard Long Video",
            description="Long-form content",
            thumbnail="videos/thumbnails/standard.jpg",
            video_file="videos/files/standard.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        self.short = Video.objects.create(
            title="Vertical Short Example",
            description="Short-form content",
            thumbnail="videos/thumbnails/short.jpg",
            video_file="videos/files/short.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.short)

    def edit_payload(self, video, content_format):
        return {
            "title": video.title,
            "description": video.description,
            "category": "",
            "channel": str(self.channel.pk),
            "publication_status": Video.PublicationStatus.PUBLISHED,
            "audience": Video.Audience.EVERYONE,
            "publish_at": "",
            "public_release_at": "",
            "content_format": content_format,
            "tags": "",
            "chapters": "",
        }

    def test_upload_form_exposes_auto_standard_video_and_short_formats(self):
        form = VideoUploadForm(user=self.creator)
        self.assertEqual(
            list(form.fields["content_format"].choices),
            [
                ("auto", "Auto-detect"),
                ("video", "Standard video"),
                ("short", "Short"),
            ],
        )
        self.assertEqual(form.fields["content_format"].initial, "auto")

    def test_edit_form_can_convert_video_to_short_and_back(self):
        form = VideoEditForm(
            self.edit_payload(self.video, "short"),
            instance=self.video,
            user=self.creator,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertTrue(VideoShort.objects.filter(video=self.video).exists())

        form = VideoEditForm(
            self.edit_payload(self.video, "video"),
            instance=self.video,
            user=self.creator,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(VideoShort.objects.filter(video=self.video).exists())

    def test_edit_form_initial_identifies_existing_short(self):
        form = VideoEditForm(instance=self.short, user=self.creator)
        self.assertEqual(form.fields["content_format"].initial, "short")

    def test_shorts_feed_contains_only_visible_shorts(self):
        hidden_short = Video.objects.create(
            title="Hidden Draft Short",
            description="",
            thumbnail="videos/thumbnails/hidden.jpg",
            video_file="videos/files/hidden.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        VideoShort.objects.create(video=hidden_short)

        response = self.client.get(reverse("shorts_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.short.title)
        self.assertNotContains(response, hidden_short.title)
        self.assertNotContains(response, self.video.title)

    def test_channel_detail_separates_shorts_and_standard_videos(self):
        response = self.client.get(reverse("channel_detail", args=[self.channel.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shorts")
        self.assertContains(response, self.short.title)
        self.assertContains(response, self.video.title)

    def test_creator_library_labels_short_format(self):
        self.client.force_login(self.creator)
        response = self.client.get(reverse("creator_video_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Short")

    def test_primary_navigation_links_to_shorts(self):
        response = self.client.get(reverse("video_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("shorts_feed"))

    def test_short_reuses_normal_video_detail_and_reporting_surface(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("video_detail", args=[self.short.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.short.title)
        self.assertContains(response, reverse("report_content", args=["video", self.short.pk]))

    def test_short_is_visible_through_existing_visibility_rules(self):
        self.assertTrue(self.short.is_visible_to(AnonymousUser()))
        self.assertIn(self.short, Video.objects.visible_to(AnonymousUser()))
