from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0031_contentreport"),
    ]

    operations = [
        migrations.CreateModel(
            name="VideoShort",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("source_start_seconds", models.PositiveIntegerField(blank=True, null=True)),
                ("source_end_seconds", models.PositiveIntegerField(blank=True, null=True)),
                ("source_video", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="derived_shorts", to="video.video")),
                ("video", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="short_metadata", to="video.video")),
            ],
        ),
    ]
