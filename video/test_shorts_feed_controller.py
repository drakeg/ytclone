from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Video
from .shorts_models import VideoShort


class ShortsFeedControllerTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="password123")
        self.short = Video.objects.create(title="Controller Short", description="Short", thumbnail="videos/short.jpg", video_file="videos/short.mp4", author=self.creator)
        VideoShort.objects.create(video=self.short)

    def test_namespaced_assets_load_only_on_shorts_feed(self):
        response = self.client.get(reverse("shorts_feed"))
        for asset in ("video/shorts.css", "video/shorts_feed.js", "video/shorts_reply_ajax.js", "video/shorts_reaction_ajax.js", "video/shorts_playback_accessibility.js", "video/shorts_share.js", "video/shorts_subscription_ajax.js"):
            self.assertContains(response, asset)
        response = self.client.get(reverse("video_list"))
        self.assertNotContains(response, "video/shorts.css")
        self.assertNotContains(response, "video/shorts_feed.js")
        self.assertNotContains(response, "video/shorts_subscription_ajax.js")

    def test_template_contains_no_inline_executable_javascript_or_stylesheet(self):
        template = Path("video/templates/videos/shorts_feed.html").read_text(encoding="utf-8")
        self.assertNotIn("<script", template)
        self.assertNotIn("IntersectionObserver", template)
        self.assertNotIn("<style", template)
        self.assertNotIn("@media(max-width:767.98px)", template)

    def test_static_stylesheet_preserves_responsive_and_reduced_motion_rules(self):
        stylesheet = Path("video/static/video/shorts.css").read_text(encoding="utf-8")
        for token in (".shorts-shell", ".shorts-feed", ".shorts-video-wrap", ".shorts-comments", "@media(max-width:767.98px)", "@media(prefers-reduced-motion:reduce)"):
            with self.subTest(token=token):
                self.assertIn(token, stylesheet)

    def test_controller_preserves_feed_initialization_and_playback_hooks(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        for token in ("document.getElementById('shorts-feed')", "if(!feed)return", "IntersectionObserver", "scrollIntoView", "visibilitychange", "prefers-reduced-motion", "data-short-play", "data-short-mute"):
            with self.subTest(token=token): self.assertIn(token, script)

    def test_feed_controller_has_no_social_ajax_ownership(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        for token in ("data-short-comment-form", "data-short-reaction-form", "data-short-share", "data-short-subscribe-form", "X-Requested-With", "new FormData(form)"):
            with self.subTest(token=token): self.assertNotIn(token, script)

    def test_discussion_controller_owns_comments_and_replies(self):
        script = Path("video/static/video/shorts_reply_ajax.js").read_text(encoding="utf-8")
        for token in ("data-short-comment-form", ".shorts-reply-form", "submitComment", "submitReply", "renderComment", "renderReply", "X-Requested-With", "new FormData(form)"):
            with self.subTest(token=token): self.assertIn(token, script)

    def test_shorts_ajax_controllers_surface_csrf_recovery_guidance(self):
        for path in (
            "video/static/video/shorts_reply_ajax.js",
            "video/static/video/shorts_reaction_ajax.js",
            "video/static/video/shorts_subscription_ajax.js",
        ):
            script = Path(path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn("response.status", script)
                self.assertIn("csrf_failed", script)
                self.assertIn("data?.message", script)
                self.assertIn("response.clone().json()", script)

    def test_feed_controller_does_not_duplicate_specialized_reaction_handler(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertNotIn("data-short-reaction-form", script)
        reaction_script = Path("video/static/video/shorts_reaction_ajax.js").read_text(encoding="utf-8")
        self.assertIn("data-short-reaction-form", reaction_script)
        self.assertIn("inFlightItems", reaction_script)

    def test_feed_controller_does_not_duplicate_specialized_share_handler(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertNotIn("data-short-share", script)
        share_script = Path("video/static/video/shorts_share.js").read_text(encoding="utf-8")
        self.assertIn("data-short-share", share_script)
        self.assertIn("navigator.share", share_script)

    def test_feed_controller_does_not_duplicate_specialized_subscription_handler(self):
        script = Path("video/static/video/shorts_feed.js").read_text(encoding="utf-8")
        self.assertNotIn("data-short-subscribe-form", script)
        subscription_script = Path("video/static/video/shorts_subscription_ajax.js").read_text(encoding="utf-8")
        self.assertIn("data-short-subscribe-form", subscription_script)
        self.assertIn("submitSubscription", subscription_script)

    def test_reaction_forms_remain_server_rendered_fallbacks(self):
        viewer = User.objects.create_user(username="reaction-viewer", password="password123")
        self.client.force_login(viewer)
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "data-short-reaction-form", count=2)
        self.assertContains(response, reverse("like_short", args=[self.short.pk]))
        self.assertContains(response, reverse("dislike_short", args=[self.short.pk]))
