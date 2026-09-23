import random

from .terrain import download_dem, download_osm_roads, generate_slope_raster, populate_road_distances, populate_terrain_data, save_osm_roads
from rest_framework import serializers
from .models import ConnectionCode, GridCell, Project, Membership, ThreatClass, ProjectThreatClass, Incident, Device, Patrol
from users.models import User
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import GEOSGeometry
import json
from users.serializers import UserSerializer
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection, transaction
from rest_framework_gis.fields import GeometryField
from django.conf import settings
from django.utils import timezone

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = Membership
        fields = '__all__'
        ready_only = ['user']

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

    grid_cells = []

    for index, row in enumerate(rows):
        geometry = GEOSGeometry(row[0])

        grid_cells.append(GridCell(
            project=project,
            geometry=geometry,
            risk_score=random.random(),
            identifier=f"cell-{index}"
        ))

    GridCell.objects.bulk_create(
        grid_cells,
        ignore_conflicts=True
    )

    # get slope and elevation data from OpenTopography
    dem_path = settings.BASE_DIR / "data" / "dem" / f"project_{project.id}_dem.tif"
    slope_path = settings.BASE_DIR / "data" / "dem" / f"project_{project.id}_slope.tif"
    download_dem(
        project,
        dem_path
    )

    generate_slope_raster(
        dem_path,
        slope_path
    )

    populate_terrain_data(project, dem_path, slope_path)

    # get distance to roads from Overpass
    data = download_osm_roads(project)
    save_osm_roads(data)
    populate_road_distances(project)

class GridCellSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = GridCell

        geo_field = "geometry"

        fields = [
            "id",
            "identifier",
            "risk_score",
            "elevation",
            "slope"
        ]

class ProjectSerializer(GeoFeatureModelSerializer):
    members = ProjectMemberSerializer(many=True, required=False)
    threat_classes = ProjectThreatClassSerializer(many=True, required=False)
    # grid_cells = GridCellSerializer(many=True, required=False)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['owner']
        geo_field = "monitoring_area"

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        threat_classes = validated_data.pop("threat_classes", [])

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

        # create membership for owner
        Membership.objects.create(
            project=project,
            user=project.owner,
            role=Membership.Role.OWNER,
            accepted=True,
            join_date=timezone.now()
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

class IncidentSerializer(serializers.ModelSerializer):
    threat_class = ThreatClassSerializer()
    device = DeviceSerializer()

    class Meta:
        model = Incident
        fields = '__all__'

class MembershipUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

class PatrolAssignerSerializer(serializers.ModelSerializer):
    user = MembershipUserSerializer()
    class Meta:
        model = Membership
        fields = ['user', 'role']

class PatrolProjectNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id','name']

class PatrolSerializer(serializers.ModelSerializer):
    incident = IncidentSerializer()
    project = PatrolProjectNameSerializer()
    assigned_by = PatrolAssignerSerializer()
    class Meta:
        model = Patrol
        fields = '__all__'
        geo_field = 'target'

class DeviceConnectSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    coordinate = GeometryField()
    battery = serializers.IntegerField()

    def validate_coordinate(self, value):
        if value.geom_type != "Point":
            raise serializers.ValidationError("Coordinate must be a Point.")
        return value