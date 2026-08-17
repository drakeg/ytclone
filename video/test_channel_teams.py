from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .forms import VideoUploadForm
from .models import Category, Channel, ChannelMembership, Video


class ChannelTeamTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.editor = User.objects.create_user(username="editor", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.category = Category.objects.create(name="General", description="General", thumbnail="categories/general.jpg")
        self.channel = Channel.objects.create(name="Owner channel", description="Owner", thumbnail="channels/owner.jpg", owner=self.owner)
        self.foreign_channel = Channel.objects.create(name="Foreign channel", description="Foreign", thumbnail="channels/foreign.jpg", owner=self.other)
        self.video = Video.objects.create(title="Team video", description="Team", thumbnail="videos/team.jpg", video_file="videos/team.mp4", author=self.owner, channel=self.channel, category=self.category)

    def add_editor(self):
        return ChannelMembership.objects.create(channel=self.channel, user=self.editor)

    def make_thumbnail(self):
        image_bytes = BytesIO()
        Image.new("RGB", (8, 8)).save(image_bytes, format="JPEG")
        return SimpleUploadedFile(
            "thumbnail.jpg", image_bytes.getvalue(), content_type="image/jpeg"
        )

    def test_team_page_requires_owner(self):
        url = reverse("channel_team", kwargs={"pk": self.channel.pk})
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.login(username="editor", password="password123")
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.logout()
        self.client.login(username="owner", password="password123")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_owner_can_add_editor_by_exact_username(self):
        self.client.login(username="owner", password="password123")
        response = self.client.post(reverse("channel_team", kwargs={"pk": self.channel.pk}), {"username": "editor"})
        self.assertRedirects(response, reverse("channel_team", kwargs={"pk": self.channel.pk}))
        self.assertTrue(ChannelMembership.objects.filter(channel=self.channel, user=self.editor).exists())

    def test_invalid_self_duplicate_and_missing_members_are_rejected(self):
        self.add_editor()
        self.client.login(username="owner", password="password123")
        url = reverse("channel_team", kwargs={"pk": self.channel.pk})
        for username, message in (("owner", "already on the team"), ("editor", "already an editor"), ("missing", "User not found")):
            with self.subTest(username=username):
                response = self.client.post(url, {"username": username})
                self.assertContains(response, message)
        self.assertEqual(ChannelMembership.objects.count(), 1)

    def test_membership_uniqueness_is_enforced(self):
        self.add_editor()
        with self.assertRaises(IntegrityError), transaction.atomic():
            ChannelMembership.objects.create(channel=self.channel, user=self.editor)

    def test_owner_can_remove_editor_with_post_only(self):
        membership = self.add_editor()
        self.client.login(username="owner", password="password123")
        url = reverse("channel_team_remove", kwargs={"pk": self.channel.pk, "membership_pk": membership.pk})
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(ChannelMembership.objects.exists())

    def test_foreign_owner_cannot_remove_membership(self):
        membership = self.add_editor()
        self.client.login(username="other", password="password123")
        response = self.client.post(reverse("channel_team_remove", kwargs={"pk": self.channel.pk, "membership_pk": membership.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ChannelMembership.objects.exists())

    def test_upload_form_includes_owned_and_assigned_channels_only(self):
        self.add_editor()
        form = VideoUploadForm(user=self.editor)
        self.assertQuerySetEqual(form.fields["channel"].queryset, [self.channel], ordered=False)
        owner_form = VideoUploadForm(user=self.owner)
        self.assertIn(self.channel, owner_form.fields["channel"].queryset)
        self.assertNotIn(self.foreign_channel, owner_form.fields["channel"].queryset)

    @override_settings(MEDIA_ROOT="/tmp/ytclone-channel-team-tests")
    def test_editor_can_upload_to_assigned_channel(self):
        self.add_editor()
        self.client.login(username="editor", password="password123")
        response = self.client.post(
            reverse("upload"),
            {
                "title": "Editor upload",
                "description": "Uploaded by the channel team",
                "thumbnail": self.make_thumbnail(),
                "video_file": SimpleUploadedFile(
                    "video.mp4", b"video", content_type="video/mp4"
                ),
                "category": self.category.pk,
                "channel": self.channel.pk,
                "publication_status": "published",
            },
        )
        uploaded = Video.objects.get(title="Editor upload")
        self.assertRedirects(
            response, reverse("video_detail", kwargs={"pk": uploaded.pk})
        )
        self.assertEqual(uploaded.author, self.editor)
        self.assertEqual(uploaded.channel, self.channel)

    def test_editor_can_edit_assigned_channel_video(self):
        self.add_editor()
        self.client.login(username="editor", password="password123")
        response = self.client.post(reverse("video_edit", kwargs={"pk": self.video.pk}), {"title": "Edited by team", "description": "Edited", "category": self.category.pk, "channel": self.channel.pk, "publication_status": "published"})
        self.assertRedirects(response, reverse("video_detail", kwargs={"pk": self.video.pk}))
        self.video.refresh_from_db()
        self.assertEqual(self.video.title, "Edited by team")

    def test_editor_cannot_edit_foreign_channel_video(self):
        self.add_editor()
        foreign_video = Video.objects.create(title="Foreign", description="Foreign", thumbnail="videos/foreign.jpg", video_file="videos/foreign.mp4", author=self.other, channel=self.foreign_channel, category=self.category)
        self.client.login(username="editor", password="password123")
        self.assertEqual(self.client.get(reverse("video_edit", kwargs={"pk": foreign_video.pk})).status_code, 404)

    def test_editor_cannot_delete_others_video_or_view_owner_pages(self):
        self.add_editor()
        self.client.login(username="editor", password="password123")
        self.assertEqual(self.client.post(reverse("video_delete", kwargs={"pk": self.video.pk})).status_code, 404)
        self.assertEqual(self.client.get(reverse("channel_analytics", kwargs={"pk": self.channel.pk})).status_code, 404)
        self.assertEqual(self.client.get(reverse("channel_team", kwargs={"pk": self.channel.pk})).status_code, 404)

    def test_editor_sees_edit_but_not_delete_control(self):
        self.add_editor()
        self.client.login(username="editor", password="password123")
        response = self.client.get(reverse("video_detail", kwargs={"pk": self.video.pk}))
        self.assertContains(response, reverse("video_edit", kwargs={"pk": self.video.pk}))
        self.assertNotContains(response, reverse("video_delete", kwargs={"pk": self.video.pk}))
