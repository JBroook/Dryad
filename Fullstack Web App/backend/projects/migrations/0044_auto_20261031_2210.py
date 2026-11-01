from django.db import migrations

THREAT_CLASSES = [
    {
        "name": "Chainsaw",
        "description": "High-frequency acoustic signature of chainsaws"
    },
    {
        "name": "Generator",
        "description": "Continuous mechanical hum of generators"
    },
    {
        "name": "Handsaw",
        "description": "Repeated sawing sounds"
    },
    {
        "name": "Fire",
        "description": "Crackling and roaring fire sounds"
    },
    {
        "name": "Treefall",
        "description": "Large trees crashing to the ground"
    },
    {
        "name": "Vehicles",
        "description": "Engine noise from passing vehicles"
    },
    {
        "name": "Gun Shot",
        "description": "Sharp gunfire sounds"
    },
    {
        "name": "Wood Chopping",
        "description": "Repeated impacts from chopping wood"
    },
]

def seed_threat_classes(apps, schema_editor):
    ThreatClass = apps.get_model("projects", "ThreatClass")

    for threat_class in THREAT_CLASSES:
        ThreatClass.objects.update_or_create(
            name=threat_class["name"],
            defaults={
                "description": threat_class["description"]
            }
        )


def reverse_seed(apps, schema_editor):
    ThreatClass = apps.get_model("projects", "ThreatClass")

    names = [tc["name"] for tc in THREAT_CLASSES]
    ThreatClass.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_threat_classes, reverse_seed),
    ]