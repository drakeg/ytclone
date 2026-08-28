from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0033_videoshort_reframing_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="videoshort",
            name="overlay_text",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="videoshort",
            name="overlay_position",
            field=models.CharField(
                choices=[("top", "Top"), ("center", "Center"), ("bottom", "Bottom")],
                default="bottom",
                max_length=10,
            ),
        ),
    ]
