from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0046_incident_manual_report"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="confirmed_incidents_since_training",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
