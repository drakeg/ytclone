from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("video", "0023_video_bookmarks")]

    operations = [
        migrations.CreateModel(
            name="Hashtag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64, unique=True)),
                ("videos", models.ManyToManyField(blank=True, related_name="hashtags", to="video.video")),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                ("videos", models.ManyToManyField(blank=True, related_name="tags", to="video.video")),
            ],
            options={"ordering": ["name"]},
        ),
    ]
