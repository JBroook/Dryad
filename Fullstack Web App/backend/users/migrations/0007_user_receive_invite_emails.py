from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_alter_user_critical_incidents_only"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="receive_invite_emails",
            field=models.BooleanField(default=True),
        ),
    ]
