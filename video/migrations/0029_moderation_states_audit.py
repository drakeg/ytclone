from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("video", "0028_video_upload_notifications_sent_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModerationAuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=40)),
                ("target_type", models.CharField(max_length=40)),
                ("target_id", models.PositiveBigIntegerField()),
                ("reason", models.TextField(max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="moderation_audit_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.CreateModel(
            name="VideoModerationState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_publication_status", models.CharField(max_length=12)),
                ("original_publish_at", models.DateTimeField(blank=True, null=True)),
                ("hidden_at", models.DateTimeField(auto_now_add=True)),
                ("video", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="moderation_state", to="video.video")),
            ],
        ),
        migrations.CreateModel(
            name="CommunityPostModerationState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hidden_at", models.DateTimeField(auto_now_add=True)),
                ("post", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="moderation_state", to="video.communitypost")),
            ],
        ),
        migrations.CreateModel(
            name="CommunityReplyModerationState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hidden_at", models.DateTimeField(auto_now_add=True)),
                ("reply", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="moderation_state", to="video.communityreply")),
            ],
        ),
    ]
