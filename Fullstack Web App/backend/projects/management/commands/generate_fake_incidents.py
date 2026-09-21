import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from projects.models import Project, Incident, ThreatClass


class Command(BaseCommand):
    help = "Generate synthetic confirmed incidents for a Dryad project."

    def add_arguments(self, parser):
        parser.add_argument(
            "project_id",
            type=int,
            help="ID of the project to populate"
        )

        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Number of days of fake incident history to generate"
        )

        parser.add_argument(
            "--incidents",
            type=int,
            default=100,
            help="Approximate number of incidents to generate"
        )

        parser.add_argument(
            "--scenario",
            choices=[
                "random",
                "road",
                "slope",
                "boundary",
            ],
            default="road",
            help="Synthetic attacker behaviour"
        )

        parser.add_argument(
            "--seed",
            type=int,
            default=2026,
            help="Random seed for reproducibility"
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing incidents for this project first"
        )

    def handle(self, *args, **options):

        random.seed(options["seed"])

        project_id = options["project_id"]
        days = options["days"]
        requested_incidents = options["incidents"]
        scenario = options["scenario"]

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise CommandError(
                f"Project {project_id} does not exist."
            )

        cells = list(
            project.grid_cells.all()
        )

        if not cells:
            raise CommandError(
                "This project has no grid cells."
            )

        if options["clear"]:
            deleted, _ = Incident.objects.filter(
                project=project
            ).delete()

            self.stdout.write(
                f"Deleted {deleted} existing incidents."
            )

        self.stdout.write(
            f"Project: {project.name}"
        )

        self.stdout.write(
            f"Grid cells: {len(cells)}"
        )

        self.stdout.write(
            f"Scenario: {scenario}"
        )

        # ---------------------------------------------------------
        # Calculate cell weights according to attacker behaviour
        # ---------------------------------------------------------

        weights = []

        for cell in cells:

            weight = self.calculate_weight(
                cell,
                scenario
            )

            weights.append(max(weight, 0.01))

        # ---------------------------------------------------------
        # Generate incidents
        # ---------------------------------------------------------

        end_time = timezone.now()

        start_time = (
            end_time -
            timedelta(days=days)
        )

        incidents = []

        for _ in range(requested_incidents):

            cell = random.choices(
                cells,
                weights=weights,
                k=1
            )[0]

            # Random timestamp within the requested period
            random_days = random.randint(0, days - 1)
            random_hour = random.randint(0, 23)
            random_minute = random.randint(0, 59)

            timestamp = (
                start_time
                + timedelta(days=random_days)
                + timedelta(
                    hours=random_hour,
                    minutes=random_minute
                )
)

            incidents.append(
                Incident(
                    project=project,
                    grid_cell=cell,
                    timestamp=timestamp,
                    coordinates=cell.geometry.centroid,

                    # Synthetic incidents are treated as
                    # ground-truth confirmed incidents.
                    status=Incident.Status.CONFIRMED,

                    # Synthetic confidence isn't important
                    # for the risk model, but gives the records
                    # realistic values.
                    confidence=random.uniform(
                        80,
                        99
                    ),

                    threat_class=ThreatClass.objects.get(name="Chainsaw"),
                )
            )

        Incident.objects.bulk_create(
            incidents
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(incidents)} fake incidents."
            )
        )

        # ---------------------------------------------------------
        # Show distribution
        # ---------------------------------------------------------

        counts = {}

        for incident in incidents:

            identifier = incident.grid_cell.identifier

            counts[identifier] = (
                counts.get(identifier, 0) + 1
            )

        self.stdout.write(
            "\nMost frequently attacked cells:"
        )

        for identifier, count in sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]:

            self.stdout.write(
                f"  {identifier}: {count}"
            )

    def calculate_weight(self, cell, scenario):

        """
        Determine how likely a cell is to be selected.

        These are deliberately synthetic rules.
        They are NOT claims about real illegal logging behaviour.
        """

        # ---------------------------------------------------------
        # Random attacker
        # ---------------------------------------------------------

        if scenario == "random":
            return 1.0

        # ---------------------------------------------------------
        # Road-dependent attacker
        # ---------------------------------------------------------

        if scenario == "road":

            distance = cell.distance_to_road

            if distance is None:
                return 1.0

            # Strong preference for cells close to roads.
            #
            # 0m   -> ~1.0
            # 500m -> ~0.37
            # 1000m -> ~0.14
            # etc.

            return 1.0 / (
                1.0 + distance / 300.0
            )

        # ---------------------------------------------------------
        # Slope-sensitive attacker
        # ---------------------------------------------------------

        if scenario == "slope":

            slope = cell.slope

            if slope is None:
                return 1.0

            # Prefer relatively flat terrain.

            return 1.0 / (
                1.0 + slope / 5.0
            )