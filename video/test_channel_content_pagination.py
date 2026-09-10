from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Channel, Video
from .shorts_models import VideoShort


class ChannelContentPaginationTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username="creator", password="pw")
        self.channel = Channel.objects.create(name="Channel", description="", owner=self.creator)
        self.url = reverse("channel_detail", kwargs={"pk": self.channel.pk})

    def make_video(self, title, *, short=False, **overrides):
        values = {
            "title": title,
            "description": title,
            "thumbnail": f"videos/{title}.jpg",
            "video_file": f"videos/{title}.mp4",
            "author": self.creator,
            "channel": self.channel,
            "publication_status": Video.PublicationStatus.PUBLISHED,
            "audience": Video.Audience.EVERYONE,
        }
        values.update(overrides)
        video = Video.objects.create(**values)
        if short:
            VideoShort.objects.create(video=video)
        return video

    def test_channel_bounds_standard_videos_and_shorts_independently(self):
        for index in range(13):
            self.make_video(f"video-{index}")
        for index in range(9):
            self.make_video(f"short-{index}", short=True)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 12)
        self.assertEqual(response.context["videos"].paginator.num_pages, 2)
        self.assertEqual(len(response.context["shorts"]), 8)
        self.assertEqual(response.context["shorts"].paginator.num_pages, 2)

    def test_each_pagination_link_preserves_the_other_section_page(self):
        for index in range(13):
            self.make_video(f"video-{index}")
        for index in range(9):
            self.make_video(f"short-{index}", short=True)

        response = self.client.get(self.url, {"video_page": 1, "short_page": 1})

        self.assertContains(response, "?video_page=2&amp;short_page=1#channel-videos")
        self.assertContains(response, "?short_page=2&amp;video_page=1#channel-shorts")

    def test_second_pages_return_remaining_content(self):
        for index in range(13):
            self.make_video(f"video-{index}")
        for index in range(9):
            self.make_video(f"short-{index}", short=True)

        response = self.client.get(self.url, {"video_page": 2, "short_page": 2})

        self.assertEqual(len(response.context["videos"]), 1)
        self.assertEqual(len(response.context["shorts"]), 1)
        self.assertContains(response, "Videos page 2 of 2")
        self.assertContains(response, "Shorts page 2 of 2")

    def test_invalid_page_values_are_handled_safely(self):
        for index in range(13):
            self.make_video(f"video-{index}")
        for index in range(9):
            self.make_video(f"short-{index}", short=True)

        malformed = self.client.get(self.url, {"video_page": "bad", "short_page": "bad"})
        out_of_range = self.client.get(self.url, {"video_page": 999, "short_page": 999})

        self.assertEqual(malformed.context["videos"].number, 1)
        self.assertEqual(malformed.context["shorts"].number, 1)
        self.assertEqual(out_of_range.context["videos"].number, 2)
        self.assertEqual(out_of_range.context["shorts"].number, 2)

    def test_non_visible_content_does_not_enter_pagination(self):
        visible = self.make_video("visible")
        hidden = self.make_video("draft", publication_status=Video.PublicationStatus.DRAFT)
        hidden_short = self.make_video("draft-short", short=True, publication_status=Video.PublicationStatus.DRAFT)

        response = self.client.get(self.url)

        self.assertContains(response, visible.title)
        self.assertNotContains(response, hidden.title)
        self.assertNotContains(response, hidden_short.title)
        self.assertEqual(response.context["videos"].paginator.count, 1)
        self.assertEqual(response.context["shorts"].paginator.count, 0)

    def test_content_is_newest_first_with_deterministic_pk_tie_break(self):
        first = self.make_video("first")
        second = self.make_video("second")
        first_short = self.make_video("first-short", short=True)
        second_short = self.make_video("second-short", short=True)

        response = self.client.get(self.url)

        self.assertEqual(list(response.context["videos"].object_list), [second, first])
        self.assertEqual(list(response.context["shorts"].object_list), [second_short, first_short])
