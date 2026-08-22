from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Channel, ChannelMembership, Video, VideoChapter
from .services.chapters import ChapterValidationError, parse_chapters


class VideoChapterTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.editor = User.objects.create_user(username="editor", password="password123")
        self.other = User.objects.create_user(username="other", password="password123")
        self.category = Category.objects.create(name="General", description="General")
        self.channel = Channel.objects.create(owner=self.owner, name="Chapter channel", description="Chapters")
        self.video = Video.objects.create(title="Chapter video", description="Video", thumbnail="videos/t.jpg", video_file="videos/v.mp4", author=self.owner, channel=self.channel, category=self.category)

    def edit_payload(self, chapters):
        return {"title": self.video.title, "description": self.video.description, "category": self.category.pk, "channel": self.channel.pk, "publication_status": Video.PublicationStatus.PUBLISHED, "audience": Video.Audience.EVERYONE, "chapters": chapters}

    def test_parser_accepts_supported_timestamps(self):
        self.assertEqual(parse_chapters("0:00 Intro\n2:05 Topic\n1:02:03 Finale"), [(0, "Intro"), (125, "Topic"), (3723, "Finale")])

    def test_parser_rejects_invalid_lists(self):
        invalid = ["0:61 Bad", "1:00 Missing zero", "0:00 Intro\n0:00 Duplicate", "0:00 Intro\n0:59 Later\n0:30 Earlier", "0:00 " + "x" * 121, "\n".join(f"{index}:00 Part" for index in range(51))]
        for value in invalid:
            with self.subTest(value=value[:30]), self.assertRaises(ChapterValidationError):
                parse_chapters(value)

    def test_owner_can_save_replace_and_remove_chapters(self):
        self.client.force_login(self.owner)
        url = reverse("video_edit", args=[self.video.pk])
        self.assertRedirects(self.client.post(url, self.edit_payload("0:00 Intro\n1:30 Main")), reverse("video_detail", args=[self.video.pk]))
        self.assertEqual(list(self.video.chapters.values_list("start_seconds", "title")), [(0, "Intro"), (90, "Main")])
        self.client.post(url, self.edit_payload("0:00 New intro"))
        self.assertEqual(list(self.video.chapters.values_list("title", flat=True)), ["New intro"])
        self.client.post(url, self.edit_payload(""))
        self.assertFalse(self.video.chapters.exists())

    def test_invalid_edit_preserves_existing_chapters(self):
        VideoChapter.objects.create(video=self.video, start_seconds=0, title="Existing")
        self.client.force_login(self.owner)
        response = self.client.post(reverse("video_edit", args=[self.video.pk]), self.edit_payload("1:00 Invalid"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("chapters", response.context["form"].errors)
        self.assertEqual(list(self.video.chapters.values_list("title", flat=True)), ["Existing"])

    def test_assigned_editor_can_manage_chapters_but_other_user_cannot(self):
        ChannelMembership.objects.create(channel=self.channel, user=self.editor)
        url = reverse("video_edit", args=[self.video.pk])
        self.client.force_login(self.editor)
        self.assertEqual(self.client.post(url, self.edit_payload("0:00 Editor chapter")).status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url, self.edit_payload("0:00 Forged")).status_code, 404)
        self.assertEqual(self.video.chapters.get().title, "Editor chapter")

    def test_visible_detail_renders_ordered_accessible_seek_controls(self):
        VideoChapter.objects.create(video=self.video, start_seconds=0, title="Intro")
        VideoChapter.objects.create(video=self.video, start_seconds=75, title="Deep dive")
        response = self.client.get(reverse("video_detail", args=[self.video.pk]))
        self.assertContains(response, 'aria-labelledby="chapters-heading"')
        self.assertContains(response, 'data-chapter-time="75"')
        self.assertContains(response, "1:15 · Deep dive")
        self.assertLess(response.content.index(b"Intro"), response.content.index(b"Deep dive"))

    def test_chapters_cascade_only_when_video_is_permanently_deleted(self):
        VideoChapter.objects.create(video=self.video, start_seconds=0, title="Intro")
        self.video.delete()
        self.assertFalse(VideoChapter.objects.exists())
