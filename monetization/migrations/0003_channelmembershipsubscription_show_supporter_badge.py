from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("monetization", "0002_alter_monetizationtransaction_platform_fee_minor"),
    ]

    operations = [
        migrations.AddField(
            model_name="channelmembershipsubscription",
            name="show_supporter_badge",
            field=models.BooleanField(default=False),
        ),
    ]
