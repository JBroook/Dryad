from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0048_membership_opened"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="retraining_threshold",
            field=models.PositiveSmallIntegerField(
                default=10,
                validators=[MinValueValidator(1)],
            ),
        ),
    ]
