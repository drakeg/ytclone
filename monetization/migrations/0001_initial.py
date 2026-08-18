# Generated manually for the initial monetization domain.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("video", "0015_optional_video_category"),
    ]

    operations = [
        migrations.CreateModel(
            name="CreatorMonetizationAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("active", "Active"), ("suspended", "Suspended")], default="pending", max_length=16)),
                ("terms_accepted_at", models.DateTimeField(blank=True, null=True)),
                ("payouts_enabled", models.BooleanField(default=False)),
                ("provider", models.CharField(blank=True, max_length=32)),
                ("provider_account_id", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("channel", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="monetization_account", to="video.channel")),
            ],
        ),
        migrations.CreateModel(
            name="MembershipTier",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("price_minor", models.PositiveIntegerField()),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("monetization_account", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="membership_tiers", to="monetization.creatormonetizationaccount")),
            ],
        ),
        migrations.CreateModel(
            name="ChannelMembershipSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("active", "Active"), ("past_due", "Past due"), ("canceled", "Canceled"), ("ended", "Ended")], default="active", max_length=16)),
                ("provider_subscription_id", models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("canceled_at", models.DateTimeField(blank=True, null=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("subscriber", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="paid_channel_memberships", to=settings.AUTH_USER_MODEL)),
                ("tier", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="monetization.membershiptier")),
            ],
        ),
        migrations.CreateModel(
            name="MonetizationTransaction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("tip", "Tip"), ("membership", "Membership"), ("refund", "Refund"), ("reversal", "Reversal"), ("payout", "Payout")], max_length=16)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("succeeded", "Succeeded"), ("failed", "Failed"), ("reversed", "Reversed")], default="pending", max_length=16)),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("gross_amount_minor", models.PositiveIntegerField()),
                ("platform_fee_minor", models.PositiveIntegerField(default=0)),
                ("provider_fee_minor", models.PositiveIntegerField(default=0)),
                ("creator_net_minor", models.IntegerField(default=0)),
                ("platform_fee_bps", models.PositiveIntegerField(default=0)),
                ("idempotency_key", models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ("provider_payment_id", models.CharField(blank=True, max_length=255)),
                ("provider_event_id", models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("membership_subscription", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="transactions", to="monetization.channelmembershipsubscription")),
                ("monetization_account", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transactions", to="monetization.creatormonetizationaccount")),
                ("payer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="monetization_payments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-pk"]},
        ),
        migrations.AddConstraint(
            model_name="membershiptier",
            constraint=models.UniqueConstraint(fields=("monetization_account", "name"), name="unique_membership_tier_name_per_channel"),
        ),
        migrations.AddConstraint(
            model_name="channelmembershipsubscription",
            constraint=models.UniqueConstraint(fields=("tier", "subscriber"), name="unique_subscriber_per_membership_tier"),
        ),
    ]
