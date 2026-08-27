from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("video", "0032_videoshort"),
    ]

    operations = [
        migrations.AddField(
            model_name="videoshort",
            name="reframing_mode",
            field=models.CharField(
                choices=[
                    ("original", "Keep original frame"),
                    ("vertical_left", "Vertical 9:16 — focus left"),
                    ("vertical_center", "Vertical 9:16 — focus center"),
                    ("vertical_right", "Vertical 9:16 — focus right"),
                ],
                default="original",
                max_length=20,
            ),
        ),
    ]
