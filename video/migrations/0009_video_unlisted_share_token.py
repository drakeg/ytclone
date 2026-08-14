import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("video", "0008_video_publication")]

    operations = [
        migrations.AlterField(
            model_name="video",
            name="publication_status",
            field=models.CharField(choices=[("draft", "Draft"), ("unlisted", "Unlisted"), ("scheduled", "Scheduled"), ("published", "Published")], default="published", max_length=12),
        ),
        migrations.AddField(
            model_name="video",
            name="share_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
