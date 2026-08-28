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
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "submitComment(form)")
        self.assertContains(response, "renderComment(form,data)")
        self.assertContains(response, "'X-Requested-With':'XMLHttpRequest'")
        self.assertContains(response, "'Accept':'application/json'")
        self.assertContains(response, "commentForms.forEach")

    def test_comment_rendering_uses_text_content_not_server_html(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "author.textContent='@'+data.author")
        self.assertContains(response, "body.textContent=data.comment")
        self.assertNotContains(response, "innerHTML=data.comment")

    def test_comment_ui_updates_count_and_exposes_failure_status(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "count.textContent=data.comment_count")
        self.assertContains(response, "Could not post comment.")
        self.assertContains(response, "if(!response.ok)throw new Error")
