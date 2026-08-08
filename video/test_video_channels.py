from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .forms import VideoUploadForm
from .models import Category, Channel, Notification, Video


class VideoChannelOwnershipTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.subscriber = User.objects.create_user(username="subscriber", password="password123")
        self.category = Category.objects.create(name="General", description="General", thumbnail="categories/general.jpg")
        self.channel = Channel.objects.create(name="Creator channel", description="Creator", thumbnail="channels/creator.jpg", owner=self.creator)
        self.other_channel = Channel.objects.create(name="Other channel", description="Other", thumbnail="channels/other.jpg", owner=self.other)

    def test_upload_form_lists_only_owned_channels(self):
        form = VideoUploadForm(user=self.creator)
        self.assertEqual(list(form.fields["channel"].queryset), [self.channel])

    def test_forged_other_users_channel_is_rejected(self):
        form = VideoUploadForm(
            user=self.creator,
            data={"title": "Forged", "description": "Forged", "category": self.category.pk, "channel": self.other_channel.pk},
            files={"thumbnail": SimpleUploadedFile("thumb.jpg", b"image", content_type="image/jpeg"), "video_file": SimpleUploadedFile("video.mp4", b"video", content_type="video/mp4")},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("channel", form.errors)

    def test_creator_without_channel_gets_clear_upload_form(self):
        user = User.objects.create_user(username="no-channel", password="password123")
        form = VideoUploadForm(user=user)
        self.assertFalse(form.fields["channel"].queryset.exists())
        self.assertIn("Create a channel", form.fields["channel"].help_text)

    def test_channel_page_shows_only_explicitly_assigned_videos(self):
        assigned = Video.objects.create(title="Assigned", description="Assigned", thumbnail="videos/a.jpg", video_file="videos/a.mp4", author=self.creator, channel=self.channel, category=self.category)
        Video.objects.create(title="Other channel video", description="Other", thumbnail="videos/b.jpg", video_file="videos/b.mp4", author=self.creator, channel=self.other_channel, category=self.category)
        legacy = Video.objects.create(title="Legacy null", description="Legacy", thumbnail="videos/c.jpg", video_file="videos/c.mp4", author=self.creator, category=self.category)
        response = self.client.get(reverse("channel_detail", kwargs={"pk": self.channel.pk}))
        self.assertEqual(list(response.context["videos"]), [assigned])
        self.assertNotContains(response, legacy.title)

    def test_new_upload_notifies_channel_subscribers(self):
        self.channel.subscribers.add(self.subscriber, self.creator)
        video = Video.objects.create(title="New", description="New", thumbnail="videos/new.jpg", video_file="videos/new.mp4", author=self.creator, channel=self.channel, category=self.category)
        from .services.notifications import notify_new_upload
        self.assertEqual(notify_new_upload(video), 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.recipient, self.subscriber)
        self.assertEqual(notification.kind, Notification.Kind.UPLOAD)
        self.assertEqual(notification.video, video)

    def test_null_channel_video_remains_supported(self):
        video = Video.objects.create(title="Legacy", description="Legacy", thumbnail="videos/legacy.jpg", video_file="videos/legacy.mp4", author=self.creator, category=self.category)
        self.assertIsNone(video.channel)
