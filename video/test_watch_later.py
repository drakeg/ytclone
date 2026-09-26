from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Playlist, PlaylistItem, Video, WatchHistory
from .services.watch_later import WATCH_LATER_NAME, get_watch_later_playlist, watch_later_videos


class WatchLaterTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username="viewer", password="password")
        self.other = User.objects.create_user(username="other", password="password")
        self.creator = User.objects.create_user(username="creator", password="password")
        self.video = Video.objects.create(
            title="Save me",
            description="Description",
            thumbnail="videos/thumbnails/test.jpg",
            video_file="videos/files/test.mp4",
            author=self.creator,
        )

    def test_page_and_mutations_require_login(self):
        self.assertEqual(self.client.get(reverse("watch_later")).status_code, 302)
        self.assertEqual(self.client.post(reverse("watch_later_add", args=[self.video.pk])).status_code, 302)
        self.assertIsNone(get_watch_later_playlist(self.viewer))

    def test_add_is_idempotent_and_collection_is_private(self):
        self.client.force_login(self.viewer)
        url = reverse("watch_later_add", args=[self.video.pk])

        self.client.post(url)
        self.client.post(url)

        playlist = get_watch_later_playlist(self.viewer)
        self.assertEqual(playlist.name, WATCH_LATER_NAME)
        self.assertEqual(playlist.visibility, Playlist.Visibility.PRIVATE)
        self.assertEqual(PlaylistItem.objects.filter(playlist=playlist, video=self.video).count(), 1)

    def test_remove_only_changes_current_viewers_collection(self):
        viewer_playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        other_playlist = Playlist.objects.create(owner=self.other, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        PlaylistItem.objects.create(playlist=viewer_playlist, video=self.video)
        PlaylistItem.objects.create(playlist=other_playlist, video=self.video)
        self.client.force_login(self.viewer)

        self.client.post(reverse("watch_later_remove", args=[self.video.pk]))

        self.assertFalse(PlaylistItem.objects.filter(playlist=viewer_playlist, video=self.video).exists())
        self.assertTrue(PlaylistItem.objects.filter(playlist=other_playlist, video=self.video).exists())

    def test_queue_uses_video_visibility_rules(self):
        hidden = Video.objects.create(
            title="Hidden",
            description="Description",
            thumbnail="videos/thumbnails/hidden.jpg",
            video_file="videos/files/hidden.mp4",
            author=self.creator,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        PlaylistItem.objects.create(playlist=playlist, video=self.video, position=0)
        PlaylistItem.objects.create(playlist=playlist, video=hidden, position=1)

        self.assertEqual(list(watch_later_videos(self.viewer)), [self.video])

    def test_page_renders_saved_video_and_remove_action(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"))

        self.assertContains(response, "Save me")
        self.assertContains(response, "Remove from Watch Later")
        self.assertContains(response, reverse("watch_later_remove", args=[self.video.pk]))

    def test_video_cards_offer_watch_later_action_to_signed_in_viewer(self):
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("video_list"))

        self.assertContains(response, "Watch Later")
        self.assertContains(response, reverse("watch_later_add", args=[self.video.pk]))

    def test_navigation_links_to_watch_later(self):
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("video_list"))

        self.assertContains(response, f'href="{reverse("watch_later")}"')

    def test_watch_later_paginates_at_24_newest_saved_first(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        saved_videos = []
        for index in range(25):
            video = Video.objects.create(
                title=f"Saved video {index:02d}",
                description="Description",
                thumbnail=f"videos/thumbnails/{index}.jpg",
                video_file=f"videos/files/{index}.mp4",
                author=self.creator,
            )
            saved_videos.append(video)
            PlaylistItem.objects.create(playlist=playlist, video=video, position=index)
        self.client.force_login(self.viewer)

        first_page = self.client.get(reverse("watch_later"))
        second_page = self.client.get(reverse("watch_later"), {"page": 2})

        self.assertEqual(first_page.context["videos"].paginator.per_page, 24)
        self.assertEqual(first_page.context["videos"].paginator.count, 25)
        self.assertContains(first_page, saved_videos[-1].title)
        self.assertNotContains(first_page, saved_videos[0].title)
        self.assertContains(first_page, "?page=2")
        self.assertContains(second_page, saved_videos[0].title)
        self.assertNotContains(second_page, saved_videos[-1].title)
        self.assertContains(second_page, "?page=1")

    def test_visibility_filter_runs_before_watch_later_pagination(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        for index in range(24):
            video = Video.objects.create(
                title=f"Visible saved {index:02d}",
                description="Description",
                thumbnail=f"videos/thumbnails/visible-{index}.jpg",
                video_file=f"videos/files/visible-{index}.mp4",
                author=self.creator,
            )
            PlaylistItem.objects.create(playlist=playlist, video=video, position=index)
        hidden = Video.objects.create(
            title="Hidden saved item",
            description="Description",
            thumbnail="videos/thumbnails/hidden-saved.jpg",
            video_file="videos/files/hidden-saved.mp4",
            author=self.creator,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        PlaylistItem.objects.create(playlist=playlist, video=hidden, position=24)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"))

        self.assertEqual(response.context["videos"].paginator.count, 24)
        self.assertEqual(response.context["videos"].paginator.num_pages, 1)
        self.assertNotContains(response, hidden.title)

    def test_invalid_watch_later_page_falls_back_safely(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"), {"page": "not-a-page"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["videos"].number, 1)
        self.assertContains(response, self.video.title)

    def test_watch_later_search_filters_titles_case_insensitively(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        match = Video.objects.create(title="Finger Lakes Adventure", description="Description", thumbnail="videos/thumbnails/match.jpg", video_file="videos/files/match.mp4", author=self.creator)
        other = Video.objects.create(title="Mountain Drive", description="Description", thumbnail="videos/thumbnails/other.jpg", video_file="videos/files/other.mp4", author=self.creator)
        PlaylistItem.objects.create(playlist=playlist, video=match, position=0)
        PlaylistItem.objects.create(playlist=playlist, video=other, position=1)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"), {"q": "finger lakes"})

        self.assertContains(response, match.title)
        self.assertNotContains(response, other.title)
        self.assertEqual(response.context["query"], "finger lakes")

    def test_watch_later_search_applies_visibility_before_filtering(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        hidden = Video.objects.create(title="Secret Trail", description="Description", thumbnail="videos/thumbnails/secret.jpg", video_file="videos/files/secret.mp4", author=self.creator, publication_status=Video.PublicationStatus.DRAFT)
        PlaylistItem.objects.create(playlist=playlist, video=hidden)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"), {"q": "secret"})

        self.assertEqual(response.context["videos"].paginator.count, 0)
        self.assertNotContains(response, hidden.title)

    def test_watch_later_search_pagination_preserves_query(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        for index in range(25):
            video = Video.objects.create(title=f"Trail video {index:02d}", description="Description", thumbnail=f"videos/thumbnails/trail-{index}.jpg", video_file=f"videos/files/trail-{index}.mp4", author=self.creator)
            PlaylistItem.objects.create(playlist=playlist, video=video, position=index)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"), {"q": "trail"})

        self.assertEqual(response.context["videos"].paginator.count, 25)
        self.assertContains(response, "?q=trail&page=2")

    def test_watch_later_remove_preserves_filtered_page(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.post(reverse("watch_later_remove", args=[self.video.pk]), {"source": "watch_later", "q": "Save me", "page": "2"})

        self.assertRedirects(response, f'{reverse("watch_later")}?q=Save+me&page=2', fetch_redirect_response=False)

    def test_whitespace_only_watch_later_search_is_unfiltered(self):
        playlist = Playlist.objects.create(owner=self.viewer, name=WATCH_LATER_NAME, visibility=Playlist.Visibility.PRIVATE)
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"), {"q": "   "})

        self.assertEqual(response.context["query"], "")
        self.assertEqual(response.context["videos"].paginator.count, 1)
        self.assertContains(response, self.video.title)

    def test_watch_later_supports_bounded_sort_options(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        alpha = Video.objects.create(
            title="Alpha video",
            description="Description",
            thumbnail="videos/thumbnails/alpha.jpg",
            video_file="videos/files/alpha.mp4",
            author=self.creator,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video, position=0)
        PlaylistItem.objects.create(playlist=playlist, video=alpha, position=1)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"), {"sort": "title"})

        self.assertEqual(list(response.context["videos"].object_list), [alpha, self.video])
        self.assertEqual(response.context["sort"], "title")

    def test_invalid_watch_later_sort_falls_back_to_newest(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video, position=0)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"), {"sort": "bogus"})

        self.assertEqual(response.context["sort"], "newest")
        self.assertContains(response, self.video.title)

    def test_watch_later_sort_composes_with_search_and_pagination(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        for index in range(25):
            video = Video.objects.create(
                title=f"Trail video {index:02d}",
                description="Description",
                thumbnail=f"videos/thumbnails/sort-{index}.jpg",
                video_file=f"videos/files/sort-{index}.mp4",
                author=self.creator,
            )
            PlaylistItem.objects.create(playlist=playlist, video=video, position=index)
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("watch_later"),
            {"q": "trail", "sort": "title"},
        )

        self.assertEqual(response.context["videos"].paginator.count, 25)
        self.assertEqual(response.context["videos"].object_list[0].title, "Trail video 00")
        self.assertContains(response, "q=trail&sort=title&page=2")

    def test_watch_later_remove_preserves_query_sort_and_page(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("watch_later_remove", args=[self.video.pk]),
            {
                "source": "watch_later",
                "q": "Save me",
                "sort": "title",
                "page": "2",
            },
        )

        self.assertRedirects(
            response,
            f'{reverse("watch_later")}?q=Save+me&sort=title&page=2',
            fetch_redirect_response=False,
        )

    def test_watch_later_oldest_sort_orders_oldest_saved_first(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        older = Video.objects.create(
            title="Older saved video",
            description="Description",
            thumbnail="videos/thumbnails/older.jpg",
            video_file="videos/files/older.mp4",
            author=self.creator,
        )
        newer = Video.objects.create(
            title="Newer saved video",
            description="Description",
            thumbnail="videos/thumbnails/newer.jpg",
            video_file="videos/files/newer.mp4",
            author=self.creator,
        )
        PlaylistItem.objects.create(playlist=playlist, video=older, position=0)
        PlaylistItem.objects.create(playlist=playlist, video=newer, position=1)
        self.client.force_login(self.viewer)

        response = self.client.get(reverse("watch_later"), {"sort": "oldest"})

        self.assertEqual(response.context["sort"], "oldest")
        self.assertEqual(
            list(response.context["videos"].object_list),
            [older, newer],
        )

    def test_watch_later_remove_control_preserves_query_sort_and_page(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.get(
            reverse("watch_later"),
            {"q": "Save me", "sort": "oldest", "page": "2"},
        )

        self.assertContains(response, 'name="q" value="Save me"')
        self.assertContains(response, 'name="sort" value="oldest"')
        self.assertContains(response, 'name="page" value="1"')



    def test_bulk_remove_removes_selected_visible_videos(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        second = Video.objects.create(
            title="Second saved",
            description="Description",
            thumbnail="videos/thumbnails/second-saved.jpg",
            video_file="videos/files/second-saved.mp4",
            author=self.creator,
        )
        keep = Video.objects.create(
            title="Keep saved",
            description="Description",
            thumbnail="videos/thumbnails/keep-saved.jpg",
            video_file="videos/files/keep-saved.mp4",
            author=self.creator,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        PlaylistItem.objects.create(playlist=playlist, video=second)
        PlaylistItem.objects.create(playlist=playlist, video=keep)
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("watch_later_bulk_remove"),
            {"video_ids": [str(self.video.pk), str(second.pk)]},
        )

        self.assertRedirects(response, reverse("watch_later"))
        self.assertFalse(
            PlaylistItem.objects.filter(
                playlist=playlist,
                video_id__in=[self.video.pk, second.pk],
            ).exists()
        )
        self.assertTrue(
            PlaylistItem.objects.filter(playlist=playlist, video=keep).exists()
        )

    def test_bulk_remove_is_post_only_and_scoped_to_viewer_and_visibility(self):
        viewer_playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        other_playlist = Playlist.objects.create(
            owner=self.other,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        hidden = Video.objects.create(
            title="Hidden saved",
            description="Description",
            thumbnail="videos/thumbnails/hidden-bulk.jpg",
            video_file="videos/files/hidden-bulk.mp4",
            author=self.creator,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        PlaylistItem.objects.create(playlist=viewer_playlist, video=self.video)
        PlaylistItem.objects.create(playlist=viewer_playlist, video=hidden)
        PlaylistItem.objects.create(playlist=other_playlist, video=self.video)
        self.client.force_login(self.viewer)
        url = reverse("watch_later_bulk_remove")

        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(
            url,
            {"video_ids": [str(self.video.pk), str(hidden.pk)]},
        )

        self.assertFalse(
            PlaylistItem.objects.filter(
                playlist=viewer_playlist, video=self.video
            ).exists()
        )
        self.assertTrue(
            PlaylistItem.objects.filter(
                playlist=viewer_playlist, video=hidden
            ).exists()
        )
        self.assertTrue(
            PlaylistItem.objects.filter(
                playlist=other_playlist, video=self.video
            ).exists()
        )

    def test_bulk_remove_ignores_empty_malformed_duplicate_and_unsaved_ids(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        unsaved = Video.objects.create(
            title="Not saved",
            description="Description",
            thumbnail="videos/thumbnails/not-saved.jpg",
            video_file="videos/files/not-saved.mp4",
            author=self.creator,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)
        url = reverse("watch_later_bulk_remove")

        empty = self.client.post(url, {})
        self.assertRedirects(empty, reverse("watch_later"))
        self.assertTrue(
            PlaylistItem.objects.filter(playlist=playlist, video=self.video).exists()
        )

        response = self.client.post(
            url,
            {
                "video_ids": [
                    str(self.video.pk),
                    str(self.video.pk),
                    "bad-id",
                    "",
                    str(unsaved.pk),
                ]
            },
        )
        self.assertRedirects(response, reverse("watch_later"))
        self.assertFalse(
            PlaylistItem.objects.filter(playlist=playlist, video=self.video).exists()
        )
        self.assertFalse(
            PlaylistItem.objects.filter(playlist=playlist, video=unsaved).exists()
        )

    def test_bulk_remove_preserves_query_sort_and_page(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("watch_later_bulk_remove"),
            {
                "video_ids": [str(self.video.pk)],
                "q": "Save me",
                "sort": "title",
                "page": "2",
            },
        )

        self.assertRedirects(
            response,
            f'{reverse("watch_later")}?q=Save+me&sort=title&page=2',
            fetch_redirect_response=False,
        )

    def test_watch_later_renders_bulk_controls_without_affecting_other_video_cards(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        watch_later_response = self.client.get(reverse("watch_later"))
        browse_response = self.client.get(reverse("video_list"))

        self.assertContains(
            watch_later_response,
            reverse("watch_later_bulk_remove"),
        )
        self.assertContains(
            watch_later_response,
            f'name="video_ids" value="{self.video.pk}"',
        )
        self.assertContains(watch_later_response, "Remove selected")
        self.assertNotContains(browse_response, 'name="video_ids"')


    def test_remove_completed_uses_continue_watching_five_second_threshold(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        completed = self.video
        incomplete = Video.objects.create(
            title="Still watching",
            description="Description",
            thumbnail="videos/thumbnails/still-watching.jpg",
            video_file="videos/files/still-watching.mp4",
            author=self.creator,
        )
        unknown = Video.objects.create(
            title="Unknown duration",
            description="Description",
            thumbnail="videos/thumbnails/unknown-duration.jpg",
            video_file="videos/files/unknown-duration.mp4",
            author=self.creator,
        )
        PlaylistItem.objects.create(playlist=playlist, video=completed)
        PlaylistItem.objects.create(playlist=playlist, video=incomplete)
        PlaylistItem.objects.create(playlist=playlist, video=unknown)
        WatchHistory.objects.create(
            user=self.viewer,
            video=completed,
            playback_position_seconds=115,
            duration_seconds=120,
        )
        WatchHistory.objects.create(
            user=self.viewer,
            video=incomplete,
            playback_position_seconds=114,
            duration_seconds=120,
        )
        WatchHistory.objects.create(
            user=self.viewer,
            video=unknown,
            playback_position_seconds=50,
            duration_seconds=0,
        )
        self.client.force_login(self.viewer)

        response = self.client.post(reverse("watch_later_remove_completed"))

        self.assertRedirects(response, reverse("watch_later"))
        self.assertFalse(
            PlaylistItem.objects.filter(playlist=playlist, video=completed).exists()
        )
        self.assertTrue(
            PlaylistItem.objects.filter(playlist=playlist, video=incomplete).exists()
        )
        self.assertTrue(
            PlaylistItem.objects.filter(playlist=playlist, video=unknown).exists()
        )

    def test_remove_completed_is_post_only_private_and_visibility_scoped(self):
        viewer_playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        other_playlist = Playlist.objects.create(
            owner=self.other,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        hidden = Video.objects.create(
            title="Hidden completed",
            description="Description",
            thumbnail="videos/thumbnails/hidden-completed.jpg",
            video_file="videos/files/hidden-completed.mp4",
            author=self.creator,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        PlaylistItem.objects.create(playlist=viewer_playlist, video=self.video)
        PlaylistItem.objects.create(playlist=viewer_playlist, video=hidden)
        PlaylistItem.objects.create(playlist=other_playlist, video=self.video)
        WatchHistory.objects.create(
            user=self.viewer,
            video=self.video,
            playback_position_seconds=118,
            duration_seconds=120,
        )
        WatchHistory.objects.create(
            user=self.viewer,
            video=hidden,
            playback_position_seconds=118,
            duration_seconds=120,
        )
        self.client.force_login(self.viewer)
        url = reverse("watch_later_remove_completed")

        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)

        self.assertFalse(
            PlaylistItem.objects.filter(
                playlist=viewer_playlist, video=self.video
            ).exists()
        )
        self.assertTrue(
            PlaylistItem.objects.filter(
                playlist=viewer_playlist, video=hidden
            ).exists()
        )
        self.assertTrue(
            PlaylistItem.objects.filter(
                playlist=other_playlist, video=self.video
            ).exists()
        )

    def test_remove_completed_preserves_query_sort_and_page(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        WatchHistory.objects.create(
            user=self.viewer,
            video=self.video,
            playback_position_seconds=118,
            duration_seconds=120,
        )
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse("watch_later_remove_completed"),
            {"q": "Save me", "sort": "title", "page": "2"},
        )

        self.assertRedirects(
            response,
            f'{reverse("watch_later")}?q=Save+me&sort=title&page=2',
            fetch_redirect_response=False,
        )

    def test_remove_watched_action_renders_only_when_completed_items_exist(self):
        playlist = Playlist.objects.create(
            owner=self.viewer,
            name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video)
        self.client.force_login(self.viewer)

        before = self.client.get(reverse("watch_later"))
        self.assertNotContains(before, "Remove watched")

        WatchHistory.objects.create(
            user=self.viewer,
            video=self.video,
            playback_position_seconds=118,
            duration_seconds=120,
        )
        after = self.client.get(reverse("watch_later"))

        self.assertContains(after, "Remove watched (1)")
        self.assertContains(after, reverse("watch_later_remove_completed"))


    def test_manual_sort_and_move_controls(self):
        playlist = Playlist.objects.create(
            owner=self.viewer, name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        second = Video.objects.create(
            title="Other queued video", description="Description",
            thumbnail="videos/thumbnails/manual.jpg",
            video_file="videos/files/manual.mp4", author=self.creator,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video, position=0)
        PlaylistItem.objects.create(playlist=playlist, video=second, position=1)
        self.client.force_login(self.viewer)
        default = self.client.get(reverse("watch_later"))
        manual = self.client.get(reverse("watch_later"), {"sort": "manual"})
        self.assertNotContains(default, 'Move up')
        self.assertEqual(list(manual.context["videos"].object_list), [self.video, second])
        self.assertContains(manual, 'Move up')
        self.assertContains(manual, reverse("watch_later_move", args=[second.pk, "up"]))

        response = self.client.post(
            reverse("watch_later_move", args=[second.pk, "up"]),
            {"q": "queued & video", "page": "2"},
        )
        self.assertRedirects(
            response,
            f'{reverse("watch_later")}?q=queued+%26+video&sort=manual&page=2',
            fetch_redirect_response=False,
        )
        reordered = self.client.get(reverse("watch_later"), {"sort": "manual"})
        self.assertEqual(list(reordered.context["videos"].object_list), [second, self.video])

    def test_manual_move_skips_hidden_items_and_preserves_them(self):
        playlist = Playlist.objects.create(
            owner=self.viewer, name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        hidden = Video.objects.create(
            title="Hidden queued", description="Description",
            thumbnail="videos/thumbnails/hidden-manual.jpg",
            video_file="videos/files/hidden-manual.mp4", author=self.creator,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        later = Video.objects.create(
            title="Later visible", description="Description",
            thumbnail="videos/thumbnails/later-manual.jpg",
            video_file="videos/files/later-manual.mp4", author=self.creator,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video, position=0)
        hidden_item = PlaylistItem.objects.create(
            playlist=playlist, video=hidden, position=1,
        )
        PlaylistItem.objects.create(playlist=playlist, video=later, position=2)
        self.client.force_login(self.viewer)
        self.client.post(reverse("watch_later_move", args=[later.pk, "up"]))
        self.assertEqual(
            list(self.client.get(
                reverse("watch_later"), {"sort": "manual"}
            ).context["videos"].object_list),
            [later, self.video],
        )
        self.assertTrue(PlaylistItem.objects.filter(pk=hidden_item.pk).exists())

    def test_manual_move_rejects_forged_unsaved_and_inaccessible_videos(self):
        playlist = Playlist.objects.create(
            owner=self.viewer, name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        other_playlist = Playlist.objects.create(
            owner=self.other, name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        hidden = Video.objects.create(
            title="Private queued", description="Description",
            thumbnail="videos/thumbnails/private-manual.jpg",
            video_file="videos/files/private-manual.mp4", author=self.creator,
            publication_status=Video.PublicationStatus.DRAFT,
        )
        PlaylistItem.objects.create(playlist=playlist, video=hidden, position=0)
        PlaylistItem.objects.create(playlist=other_playlist, video=self.video, position=0)
        self.client.force_login(self.viewer)
        url = reverse("watch_later_move", args=[self.video.pk, "up"])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertEqual(
            self.client.post(
                reverse("watch_later_move", args=[hidden.pk, "up"])
            ).status_code, 404,
        )
        self.assertEqual(
            self.client.post(
                reverse("watch_later_move", args=[hidden.pk, "sideways"])
            ).status_code, 404,
        )
        self.assertEqual(other_playlist.items.count(), 1)

    def test_manual_move_boundary_is_noop_and_other_sorts_remain_available(self):
        playlist = Playlist.objects.create(
            owner=self.viewer, name=WATCH_LATER_NAME,
            visibility=Playlist.Visibility.PRIVATE,
        )
        PlaylistItem.objects.create(playlist=playlist, video=self.video, position=0)
        self.client.force_login(self.viewer)
        self.client.post(reverse("watch_later_move", args=[self.video.pk, "up"]))
        self.client.post(reverse("watch_later_move", args=[self.video.pk, "down"]))
        for sort in ("newest", "oldest", "title", "manual"):
            with self.subTest(sort=sort):
                response = self.client.get(reverse("watch_later"), {"sort": sort})
                self.assertEqual(response.context["sort"], sort)
                self.assertEqual(list(response.context["videos"].object_list), [self.video])
