import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("video", "0030_channelmoderationstate"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_type", models.CharField(choices=[("channel", "Channel"), ("video", "Video"), ("comment", "Video comment"), ("community_post", "Community post"), ("community_reply", "Community reply")], max_length=24)),
                ("target_id", models.PositiveBigIntegerField()),
                ("target_label", models.CharField(max_length=255)),
                ("reason", models.CharField(choices=[("spam", "Spam or misleading"), ("harassment", "Harassment or bullying"), ("hate", "Hate or abusive content"), ("violence", "Violence or dangerous content"), ("sexual", "Sexual or inappropriate content"), ("privacy", "Privacy or personal information"), ("copyright", "Copyright or intellectual property"), ("other", "Other")], max_length=24)),
                ("details", models.TextField(blank=True, max_length=1000)),
                ("status", models.CharField(choices=[("open", "Open"), ("resolved", "Resolved"), ("dismissed", "Dismissed")], default="open", max_length=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("resolution_note", models.TextField(blank=True, max_length=1000)),
                ("reporter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="content_reports", to=settings.AUTH_USER_MODEL)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reviewed_content_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at", "-pk"],
                "indexes": [models.Index(fields=["status", "-created_at"], name="report_status_created_idx"), models.Index(fields=["target_type", "target_id"], name="report_target_idx")],
                "constraints": [models.UniqueConstraint(condition=models.Q(("status", "open")), fields=("reporter", "target_type", "target_id"), name="unique_open_report_per_user_target")],
            },
        ),
    ]
