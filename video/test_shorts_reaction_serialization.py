from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ShortsReactionSerializationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="reaction-owner", password="password123")
        self.viewer = User.objects.create_user(username="reaction-viewer", password="password123")
        self.channel = Channel.objects.create(owner=self.creator, name="Reaction Channel", description="")
        self.video = Video.objects.create(
            title="Serialized Short",
            description="",
            thumbnail="videos/thumbnails/serialized.jpg",
            video_file="videos/files/serialized.mp4",
            author=self.creator,
            channel=self.channel,
            publication_status=Video.PublicationStatus.PUBLISHED,
        )
        VideoShort.objects.create(video=self.video)
        self.client.force_login(self.viewer)

    def test_shorts_feed_loads_serialized_reaction_handler(self):
        response = self.client.get(reverse("shorts_feed"))
        self.assertContains(response, "shorts_reaction_ajax.js")

    def test_reaction_handler_serializes_each_short(self):
        script_path = Path(__file__).resolve().parent / "static" / "shorts_reaction_ajax.js"
        script = script_path.read_text(encoding="utf-8")

        self.assertIn("new WeakSet()", script)
        self.assertIn("inFlightItems.has(item)", script)
        self.assertIn("inFlightItems.add(item)", script)
        self.assertIn("inFlightItems.delete(item)", script)
        self.assertIn("setReactionButtonsDisabled(item, true)", script)
        self.assertIn("setReactionButtonsDisabled(item, false)", script)
        self.assertIn("event.stopImmediatePropagation()", script)

    def test_handler_disables_both_reaction_forms_for_the_short(self):
        script_path = Path(__file__).resolve().parent / "static" / "shorts_reaction_ajax.js"
        script = script_path.read_text(encoding="utf-8")

        self.assertIn("item.querySelectorAll('[data-short-reaction-form] button[type=\"submit\"]')", script)
        self.assertIn("button.disabled = disabled", script)

    def test_handler_keeps_server_authoritative_state(self):
        script_path = Path(__file__).resolve().parent / "static" / "shorts_reaction_ajax.js"
        script = script_path.read_text(encoding="utf-8")

        self.assertIn('"X-Requested-With": "XMLHttpRequest"', script)
        self.assertIn("syncReaction(item, await response.json())", script)
        self.assertNotIn("optimistic", script.lower())
