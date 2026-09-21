import math
import random
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.gis.geos import Point

from projects.models import Project, Incident, ThreatClass


class Command(BaseCommand):
    help = (
        "Generate synthetic confirmed incidents with spatial "
        "and temporal attack behaviour."
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "project_id",
            type=int,
            help="ID of the project to populate",
        )

        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Number of days of fake incident history to generate",
        )

        parser.add_argument(
            "--incidents",
            type=int,
            default=5000,
            help="Approximate number of incidents to generate",
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
            help="Base environmental attacker behaviour",
        )

        parser.add_argument(
            "--seed",
            type=int,
            default=2026,
            help="Random seed for reproducibility",
        )

        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing incidents for this project first",
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

        cells = list(project.grid_cells.all())

        Incident.objects.filter(project_id=project_id).delete()
        self.stdout.write(
            f"Previous incidents deleted"
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

        threat_class = ThreatClass.objects.get(
            name="Chainsaw"
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

        self.stdout.write(
            f"Target incidents: {requested_incidents}"
        )

        # ---------------------------------------------------------
        # Pre-calculate environmental weights
        # ---------------------------------------------------------

        environmental_weights = {}

        for cell in cells:

            weight = self.calculate_environment_weight(
                cell,
                scenario,
            )

            environmental_weights[cell.id] = max(
                weight,
                0.001,
            )

        # ---------------------------------------------------------
        # Generate incidents chronologically
        # ---------------------------------------------------------

        end_time = timezone.now()

        start_time = (
            end_time -
            timedelta(days=days)
        )

        # Store previous attacks in memory.
        #
        # cell_id -> list of timestamps
        #
        attack_history = {
            cell.id: []
            for cell in cells
        }

        # Store all generated incidents.
        incidents = []

        # ---------------------------------------------------------
        # We generate incidents one at a time.
        #
        # Unlike the old generator, the probability of selecting
        # a cell now depends on attacks that have already happened.
        # ---------------------------------------------------------

        for incident_number in range(
            requested_incidents
        ):

            # Random timestamp.
            #
            # Sorting later means the temporal influence is based
            # only on incidents that happened earlier.
            timestamp = (
                start_time
                + timedelta(
                    seconds=random.randint(
                        0,
                        int(
                            (end_time - start_time)
                            .total_seconds()
                        ),
                    )
                )
            )

            # -----------------------------------------------------
            # Calculate selection weights.
            # -----------------------------------------------------

            weights = []

            for cell in cells:

                environmental_weight = (
                    environmental_weights[cell.id]
                )

                temporal_weight = (
                    self.calculate_temporal_weight(
                        cell.id,
                        timestamp,
                        attack_history,
                    )
                )

                weight = (
                    environmental_weight
                    * temporal_weight
                )

                weights.append(
                    max(weight, 0.001)
                )

            # -----------------------------------------------------
            # Select cell.
            # -----------------------------------------------------

            cell = random.choices(
                cells,
                weights=weights,
                k=1,
            )[0]

            # -----------------------------------------------------
            # Store attack history.
            # -----------------------------------------------------

            attack_history[cell.id].append(
                timestamp
            )

            incidents.append(
                {
                    "project": project,
                    "grid_cell": cell,
                    "timestamp": timestamp,
                    "coordinates": cell.geometry.centroid,
                    "status": Incident.Status.CONFIRMED,
                    "confidence": random.uniform(
                        80,
                        99,
                    ),
                    "threat_class": threat_class,
                }
            )

            # Progress indicator.
            if (
                incident_number + 1
            ) % 1000 == 0:

                self.stdout.write(
                    f"Generated "
                    f"{incident_number + 1}/"
                    f"{requested_incidents}"
                )

        # ---------------------------------------------------------
        # Sort chronologically before creating database records.
        # ---------------------------------------------------------

        incidents.sort(
            key=lambda incident: incident["timestamp"]
        )

        incident_objects = [
            Incident(**incident)
            for incident in incidents
        ]

        Incident.objects.bulk_create(
            incident_objects
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created "
                f"{len(incident_objects)} "
                f"synthetic incidents."
            )
        )

        # ---------------------------------------------------------
        # Show most frequently attacked cells.
        # ---------------------------------------------------------

        counts = {}

        for incident in incident_objects:

            identifier = (
                incident.grid_cell.identifier
            )

            counts[identifier] = (
                counts.get(identifier, 0)
                + 1
            )

        self.stdout.write(
            "\nMost frequently attacked cells:"
        )

        for identifier, count in sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]:

            self.stdout.write(
                f"  {identifier}: {count}"
            )

    # =============================================================
    # ENVIRONMENTAL BEHAVIOUR
    # =============================================================

    def calculate_environment_weight(
        self,
        cell,
        scenario,
    ):
        """
        Calculate the base probability weight based on
        environmental characteristics.

        These are synthetic assumptions used to test
        the machine-learning pipeline.
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

            return 1.0 / (
                1.0 +
                (distance / 150.0) ** 2
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
                1.0 +
                slope / 5.0
            )

        # ---------------------------------------------------------
        # Boundary-dependent attacker
        # ---------------------------------------------------------

        if scenario == "boundary":

            distance = getattr(
                cell,
                "distance_to_boundary",
                None,
            )

            if distance is None:
                return 1.0

            return 1.0 / (
                1.0 +
                distance / 150.0
            )

        return 1.0

    # =============================================================
    # TEMPORAL BEHAVIOUR
    # =============================================================

    def calculate_temporal_weight(
        self,
        cell_id,
        timestamp,
        attack_history,
    ):
        """
        Increase the probability of an attack occurring in cells
        that have experienced recent attacks.

        The influence decays exponentially with time.

        Same cell:
            strong effect

        Nearby cell:
            not currently modelled here

        Older attack:
            weaker effect
        """

        previous_attacks = attack_history[cell_id]

        if not previous_attacks:
            return 1.0

        # ---------------------------------------------------------
        # Find most recent attack.
        # ---------------------------------------------------------

        recent_attack = max(
            previous_attacks
        )

        elapsed_hours = (
            timestamp - recent_attack
        ).total_seconds() / 3600.0

        # Safety check.
        if elapsed_hours < 0:
            return 1.0

        # ---------------------------------------------------------
        # Temporal persistence.
        #
        # Immediately after an attack:
        #
        #     weight ≈ 6
        #
        # After 1 day:
        #
        #     weight ≈ 3
        #
        # After several days:
        #
        #     approaches 1
        # ---------------------------------------------------------

        persistence = (
            5.0 *
            math.exp(
                -elapsed_hours / 72.0
            )
        )

        return 1.0 + persistence
