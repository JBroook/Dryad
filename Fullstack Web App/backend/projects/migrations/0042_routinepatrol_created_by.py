import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0041_routinepatrol"),
    ]

    operations = [
        migrations.AddField(
            model_name="routinepatrol",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_routine_patrols",
                to="projects.membership",
            ),
        ),
    ]
