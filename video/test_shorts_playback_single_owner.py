from django.test import SimpleTestCase


class ShortsPlaybackSingleOwnerTests(SimpleTestCase):
    def test_feed_controller_leaves_accessible_playback_state_to_helper(self):
        with open("video/static/video/shorts_feed.js", encoding="utf-8") as script_file:
            script = script_file.read()

        sync_play = script.split("const syncPlay=i=>", 1)[1].split(";const syncSound=", 1)[0]
        self.assertIn("b.textContent=paused?'Play':'Pause'", sync_play)
        self.assertIn("b.classList.toggle('is-paused',paused)", sync_play)
        self.assertNotIn("setAttribute('aria-label'", sync_play)
        self.assertNotIn("setAttribute('aria-pressed'", sync_play)

    def test_accessibility_helper_owns_playback_action_label(self):
        with open("video/static/video/shorts_playback_accessibility.js", encoding="utf-8") as script_file:
            script = script_file.read()

        self.assertIn('button.setAttribute("aria-label", `${action} ${title}`);', script)
        self.assertIn('button.removeAttribute("aria-pressed");', script)
