from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("video", "0010_video_deleted_at")]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="is_hidden",
            field=models.BooleanField(default=False),
        ),
    ]
