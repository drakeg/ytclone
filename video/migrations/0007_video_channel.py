from django.db import migrations, models
import django.db.models.deletion


def assign_existing_channels(apps, schema_editor):
    Video = apps.get_model("video", "Video")
    Channel = apps.get_model("video", "Channel")
    for author_id in Video.objects.values_list("author_id", flat=True).distinct():
        channel = Channel.objects.filter(owner_id=author_id).order_by("pk").first()
        if channel:
            Video.objects.filter(author_id=author_id, channel__isnull=True).update(
                channel_id=channel.pk
            )


class Migration(migrations.Migration):
    dependencies = [("video", "0006_notification")]

    operations = [
        migrations.AddField(
            model_name="video",
            name="channel",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="videos", to="video.channel"),
        ),
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(choices=[("comment", "Comment"), ("like", "Like"), ("dislike", "Dislike"), ("subscription", "Subscription"), ("upload", "New upload")], max_length=20),
        ),
        migrations.RunPython(assign_existing_channels, migrations.RunPython.noop),
    ]
