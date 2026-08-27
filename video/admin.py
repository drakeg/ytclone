from django.contrib import admin

from .community_models import (
    CommunityPollOption,
    CommunityPollVote,
    CommunityPost,
    CommunityReply,
)
from .metadata_models import Hashtag, Tag
from .models import (
    Category,
    Channel,
    ChannelMembership,
    ChannelTeamInvitation,
    Comment,
    Notification,
    Playlist,
    PlaylistItem,
    Video,
    VideoBookmark,
    VideoChapter,
    VideoWatchEvent,
    WatchHistory,
)
from .moderation_models import (
    CommunityPostModerationState,
    CommunityReplyModerationState,
    ModerationAuditEvent,
    VideoModerationState,
)
from .qa_models import VideoQuestion


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "channel",
        "author",
        "publication_status",
        "audience",
        "publish_at",
        "deleted_at",
    )
    list_filter = ("publication_status", "audience", "deleted_at", "category")
    search_fields = ("title", "description", "author__username", "channel__name")
    autocomplete_fields = ("author", "channel", "category")


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "subscriber_count")
    search_fields = ("name", "owner__username")
    autocomplete_fields = ("owner",)

    @admin.display(description="Subscribers")
    def subscriber_count(self, obj):
        return obj.subscribers.count()


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name", "description")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "video", "pub_date", "is_hidden", "parent")
    list_filter = ("is_hidden", "pub_date")
    search_fields = ("comment", "author__username", "video__title")
    autocomplete_fields = ("author", "video", "parent")


@admin.register(ChannelMembership)
class ChannelMembershipAdmin(admin.ModelAdmin):
    list_display = ("channel", "user", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("channel__name", "user__username")


@admin.register(ChannelTeamInvitation)
class ChannelTeamInvitationAdmin(admin.ModelAdmin):
    list_display = ("channel", "invitee", "invited_by", "status", "expires_at")
    list_filter = ("status",)
    search_fields = ("channel__name", "invitee__username", "invited_by__username")


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "visibility", "updated_at")
    list_filter = ("visibility",)
    search_fields = ("name", "owner__username")


@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    list_display = ("playlist", "video", "position", "added_at")
    search_fields = ("playlist__name", "video__title")


@admin.register(VideoChapter)
class VideoChapterAdmin(admin.ModelAdmin):
    list_display = ("video", "start_seconds", "title")
    search_fields = ("video__title", "title")


@admin.register(VideoBookmark)
class VideoBookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "video", "position_seconds", "label", "updated_at")
    search_fields = ("user__username", "video__title", "label")


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "video", "watched_at", "playback_position_seconds")
    search_fields = ("user__username", "video__title")
    readonly_fields = ("user", "video", "watched_at", "playback_position_seconds", "duration_seconds")


@admin.register(VideoWatchEvent)
class VideoWatchEventAdmin(admin.ModelAdmin):
    list_display = ("video", "viewer", "watched_seconds", "position_seconds", "created_at")
    search_fields = ("video__title", "viewer__username", "viewer_session_hash")
    readonly_fields = [field.name for field in VideoWatchEvent._meta.fields]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "kind", "actor", "video", "channel", "created_at", "read_at")
    list_filter = ("kind", "read_at")
    search_fields = ("recipient__username", "actor__username", "video__title", "channel__name")


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ("channel", "author", "kind", "audience", "created_at")
    list_filter = ("kind", "audience")
    search_fields = ("body", "channel__name", "author__username")


@admin.register(CommunityReply)
class CommunityReplyAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at")
    search_fields = ("body", "author__username", "post__channel__name")


@admin.register(ModerationAuditEvent)
class ModerationAuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "target_type", "target_id")
    list_filter = ("action", "target_type")
    search_fields = ("actor__username", "reason")
    readonly_fields = [field.name for field in ModerationAuditEvent._meta.fields]


admin.site.register(VideoModerationState)
admin.site.register(CommunityPostModerationState)
admin.site.register(CommunityReplyModerationState)
admin.site.register(CommunityPollOption)
admin.site.register(CommunityPollVote)
admin.site.register(Tag)
admin.site.register(Hashtag)
admin.site.register(VideoQuestion)
