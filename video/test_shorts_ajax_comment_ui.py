from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsAjaxCommentUiTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="comment-ui-creator", password="password123")
        self.viewer = User.objects.create_user(username="comment-ui-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Comment UI Channel", description="")
        self.video = Video.objects.create(
            title="Comment UI Short",
            description="AJAX comment UI test",
            thumbnail="videos/thumbnails/comment-ui.jpg",
            video_file="videos/files/comment-ui.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)
        self.client.force_login(self.viewer)

    def test_comment_form_keeps_progressive_enhancement_fallback(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-short-comment-form")
        self.assertContains(response, "data-short-comment-count")
        self.assertContains(response, reverse("add_short_comment", args=[self.video.pk]))
        self.assertContains(response, 'name="csrfmiddlewaretoken"')

    def test_feed_wires_comment_form_to_ajax_contract(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertIn("submitComment(form)", script)
        self.assertIn("renderComment(form,data)", script)
        self.assertIn("'X-Requested-With':'XMLHttpRequest'", script)
        self.assertIn("'Accept':'application/json'", script)
        self.assertIn("commentForms.forEach", script)

    def test_comment_rendering_uses_text_content_not_server_html(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertIn("author.textContent='@'+data.author", script)
        self.assertIn("body.textContent=data.comment", script)
        self.assertNotIn("innerHTML=data.comment", script)

    def test_comment_ui_updates_count_and_exposes_failure_status(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "Could not post comment.")
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertIn("count.textContent=data.comment_count", script)
        self.assertIn("if(!response.ok)throw new Error", script)
from pathlib import Path
