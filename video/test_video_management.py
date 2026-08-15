from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel, Comment, Notification, Playlist, PlaylistItem, Video, WatchHistory


class VideoManagementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.category = Category.objects.create(name="General", description="General", thumbnail="categories/general.jpg")
        self.other_category = Category.objects.create(name="Other", description="Other", thumbnail="categories/other.jpg")
        self.channel = Channel.objects.create(name="First", description="First", thumbnail="channels/first.jpg", owner=self.owner)
        self.second_channel = Channel.objects.create(name="Second", description="Second", thumbnail="channels/second.jpg", owner=self.owner)
        self.foreign_channel = Channel.objects.create(name="Foreign", description="Foreign", thumbnail="channels/foreign.jpg", owner=self.other)
        self.video = Video.objects.create(title="Original", description="Original", thumbnail="videos/original.jpg", video_file="videos/original.mp4", author=self.owner, channel=self.channel, category=self.category)

    def test_edit_requires_login_and_owner(self):
        url = reverse("video_edit", kwargs={"pk": self.video.pk})
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.login(username="other", password="password123")
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_owner_can_edit_metadata_and_move_owned_channel_without_replacing_media(self):
        old_thumbnail = self.video.thumbnail.name
        old_file = self.video.video_file.name
        self.client.login(username="owner", password="password123")
        response = self.client.post(reverse("video_edit", kwargs={"pk": self.video.pk}), {"title": "Updated", "description": "Updated description", "category": self.other_category.pk, "channel": self.second_channel.pk, "publication_status": "published"})
        self.assertRedirects(response, reverse("video_detail", kwargs={"pk": self.video.pk}))
        self.video.refresh_from_db()
        self.assertEqual(self.video.title, "Updated")
        self.assertEqual(self.video.channel, self.second_channel)
        self.assertEqual(self.video.category, self.other_category)
        self.assertEqual(self.video.thumbnail.name, old_thumbnail)
        self.assertEqual(self.video.video_file.name, old_file)

    def test_forged_foreign_channel_edit_is_rejected(self):
        self.client.login(username="owner", password="password123")
        response = self.client.post(reverse("video_edit", kwargs={"pk": self.video.pk}), {"title": "Forged", "description": "Forged", "category": self.category.pk, "channel": self.foreign_channel.pk, "publication_status": "published"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("channel", response.context["form"].errors)
        self.video.refresh_from_db()
        self.assertEqual(self.video.channel, self.channel)

    def test_management_links_are_owner_only(self):
        detail = reverse("video_detail", kwargs={"pk": self.video.pk})
        self.client.login(username="owner", password="password123")
        owner_response = self.client.get(detail)
        self.client.logout()
        self.client.login(username="other", password="password123")
        other_response = self.client.get(detail)
        self.assertContains(owner_response, reverse("video_edit", kwargs={"pk": self.video.pk}))
        self.assertNotContains(other_response, reverse("video_edit", kwargs={"pk": self.video.pk}))

    def test_delete_confirmation_is_owner_only(self):
        url = reverse("video_delete", kwargs={"pk": self.video.pk})
        self.client.login(username="other", password="password123")
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.logout()
        self.client.login(username="owner", password="password123")
        self.assertContains(self.client.get(url), "recoverable for 30 days")

    def test_post_delete_trashes_video_and_retains_related_records(self):
        Comment.objects.create(video=self.video, author=self.other, comment="Comment")
        WatchHistory.objects.create(video=self.video, user=self.other)
        playlist = Playlist.objects.create(owner=self.other, name="List")
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        Notification.objects.create(recipient=self.owner, actor=self.other, kind=Notification.Kind.LIKE, video=self.video)
        self.client.login(username="owner", password="password123")
        response = self.client.post(reverse("video_delete", kwargs={"pk": self.video.pk}))
        self.assertRedirects(response, reverse("creator_video_list"))
        self.video.refresh_from_db()
        self.assertIsNotNone(self.video.deleted_at)
        self.assertEqual(self.video.publication_status, Video.PublicationStatus.DRAFT)
        self.assertTrue(Comment.objects.exists())
        self.assertTrue(WatchHistory.objects.exists())
        self.assertTrue(PlaylistItem.objects.exists())
        self.assertTrue(Notification.objects.exists())
