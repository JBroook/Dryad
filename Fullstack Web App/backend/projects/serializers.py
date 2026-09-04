from rest_framework import serializers
from .models import GridCell, Project, Membership, ThreatClass, ProjectThreatClass, Incident, Device, Patrol
from users.models import User
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import GEOSGeometry
import json
from users.serializers import UserSerializer
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection, transaction

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Membership
        fields = '__all__'

class ProjectMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=Membership.Role.choices)

class ProjectThreatClassSerializer(serializers.Serializer):
    id = serializers.IntegerField()

@transaction.atomic
def generate_grid(project, cell_size=100):
    # Remove existing cells if we're regenerating
    project.grid_cells.all().delete()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                ST_AsEWKT(
                    ST_Transform(
                        ST_Intersection(
                            grid.geom,
                            ST_Transform(
                                p.monitoring_area,
                                32647
                            )
                        ),
                        4326
                    )
                )
            FROM projects_project p

            CROSS JOIN LATERAL
                ST_SquareGrid(
                    %s,
                    ST_Transform(
                        p.monitoring_area,
                        32647
                    )
                ) AS grid(geom)

            WHERE p.id = %s

            AND ST_Intersects(
                grid.geom,
                ST_Transform(
                    p.monitoring_area,
                    32647
                )
            )
        """, [cell_size, project.id])

        rows = cursor.fetchall()

    for index, row in enumerate(rows):
        geometry = GEOSGeometry(row[0])

        GridCell.objects.create(
            project=project,
            geometry=geometry,
            identifier=f"cell-{index}"
        )

class GridCellSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = GridCell

        geo_field = "geometry"

        fields = [
            "id",
            "identifier",
            "risk_score"
        ]

class ProjectSerializer(GeoFeatureModelSerializer):
    members = ProjectMemberSerializer(many=True, required=False)
    threat_classes = ProjectThreatClassSerializer(many=True, required=False)
    grid_cells = GridCellSerializer(many=True, required=False)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['owner', 'grid_cells']
        geo_field = "monitoring_area"

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        threat_classes = validated_data.pop("threat_classes", [])

        if "monitoring_area" in validated_data:
            geojson = validated_data["monitoring_area"]

            if geojson.get("type") == "Feature":
                geojson = geojson["geometry"]

            validated_data["monitoring_area"] = GEOSGeometry(
                json.dumps(geojson),
                srid=4326
            )

        project = Project.objects.create(**validated_data)

        # generate grid
        generate_grid(project=project, cell_size=100)

        # generate memberships
        for member in members:
            Membership.objects.create(
                project=project,
                user=User.objects.get(pk=member["id"]),
                role=member['role']
            )

        # record threat classes to detect
        for threat_class in threat_classes:
            ProjectThreatClass.objects.create(
                project=project,
                threat_class=ThreatClass.objects.get(pk=threat_class["id"])
            )

        return project


class ThreatClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreatClass
        fields = '__all__'

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class PatrolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patrol
        fields = '__all__'
        geo_field = 'target'

class IncidentSerializer(serializers.ModelSerializer):
    threat_class = ThreatClassSerializer()
    device = DeviceSerializer()

    class Meta:
        model = Incident
        fields = '__all__'