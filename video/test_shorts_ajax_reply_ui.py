from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Comment, Video
from .shorts_models import VideoShort


class ShortsAjaxReplyUiTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="reply-ui-creator", password="password123")
        self.viewer = User.objects.create_user(username="reply-ui-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Reply UI Channel", description="")
        self.video = Video.objects.create(
            title="Reply UI Short",
            description="Reply UI test",
            thumbnail="videos/thumbnails/reply-ui.jpg",
            video_file="videos/files/reply-ui.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)
        Comment.objects.create(video=self.video, author=self.creator, comment="Reply to me")
        self.client.force_login(self.viewer)

    def test_shorts_feed_loads_reply_ajax_script(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "shorts_reply_ajax.js")
        self.assertContains(response, 'class="shorts-reply-form mt-2"')

    def test_non_shorts_page_does_not_load_reply_ajax_script(self):
        response = self.client.get(reverse("video_list"))
        self.assertNotContains(response, "shorts_reply_ajax.js")

    def test_reply_script_uses_ajax_and_server_confirmed_data(self):
        script = Path("video/static/shorts_reply_ajax.js").read_text()
        self.assertIn("'.shorts-reply-form'", script)
        self.assertIn("'X-Requested-With': 'XMLHttpRequest'", script)
        self.assertIn("const data = await response.json()", script)
        self.assertIn("body.textContent = data.comment", script)
        self.assertIn("data.reply_count", script)

    def test_reply_script_preserves_text_on_failure_and_clears_after_success(self):
        script = Path("video/static/shorts_reply_ajax.js").read_text()
        self.assertIn("if (textarea) textarea.value = ''", script)
        self.assertIn("error.hidden = false", script)
        self.assertNotIn("textarea.value = ''", script.split("catch (_)", 1)[1])
