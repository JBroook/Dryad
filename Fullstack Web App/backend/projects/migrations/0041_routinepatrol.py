import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0040_patrol_members"),
    ]

    operations = [
        migrations.CreateModel(
            name="RoutinePatrol",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "frequency",
                    models.CharField(
                        choices=[
                            ("once", "Once"),
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                            ("monthly", "Monthly"),
                        ],
                        default="weekly",
                        max_length=10,
                    ),
                ),
                ("start_date", models.DateField()),
                (
                    "path",
                    django.contrib.gis.db.models.fields.LineStringField(srid=4326),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="routine_patrols",
                        to="projects.project",
                    ),
                ),
            ],
        ),
    ]
