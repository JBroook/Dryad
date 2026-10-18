import django.db.models.deletion
from django.db import migrations, models


def copy_patrol_member_to_members(apps, schema_editor):
    Patrol = apps.get_model("projects", "Patrol")

    for patrol in Patrol.objects.using(schema_editor.connection.alias).all().iterator():
        patrol.members.add(patrol.member_id)


def copy_patrol_member_from_members(apps, schema_editor):
    Patrol = apps.get_model("projects", "Patrol")

    for patrol in Patrol.objects.using(schema_editor.connection.alias).all().iterator():
        member_id = patrol.members.order_by("pk").values_list("pk", flat=True).first()
        if member_id is not None:
            patrol.member_id = member_id
            patrol.save(update_fields=["member"])


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0039_project_last_trained_project_train_count"),
    ]

    operations = [
        migrations.AlterField(
            model_name="patrol",
            name="member",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="projects.membership",
            ),
        ),
        migrations.AddField(
            model_name="patrol",
            name="members",
            field=models.ManyToManyField(to="projects.membership"),
        ),
        migrations.RunPython(
            copy_patrol_member_to_members,
            copy_patrol_member_from_members,
        ),
        migrations.RemoveField(
            model_name="patrol",
            name="member",
        ),
    ]
