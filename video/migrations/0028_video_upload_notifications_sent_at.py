from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("video", "0027_video_public_release_at")]

    operations = [
        migrations.AddField(
            model_name="video",
            name="upload_notifications_sent_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
