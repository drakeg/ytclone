from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("video", "0007_video_channel")]

    operations = [
        migrations.AddField(
            model_name="video",
            name="publication_status",
            field=models.CharField(choices=[("draft", "Draft"), ("scheduled", "Scheduled"), ("published", "Published")], default="published", max_length=12),
        ),
        migrations.AddField(
            model_name="video",
            name="publish_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
