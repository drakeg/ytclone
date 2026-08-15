from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("video", "0009_video_unlisted_share_token")]

    operations = [
        migrations.AddField(
            model_name="video",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
