import random
import logging

from .terrain import download_dem, download_osm_roads, generate_slope_raster, populate_road_distances, populate_terrain_data, save_osm_roads
from rest_framework import serializers
from .models import ConnectionCode, GridCell, Project, Membership, ThreatClass, ProjectThreatClass, Incident, Device, Patrol, RoutinePatrol
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
import requests

logger = logging.getLogger(__name__)

class ProjectOverviewSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    device_count = serializers.IntegerField(read_only=True)
    new_alerts = serializers.IntegerField(read_only=True)
    total_incidents = serializers.IntegerField(read_only=True)
    online_devices = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'color',
            'name',
            'status',
            'surface_area',
            'region',
            'member_count',
            'device_count',
            'new_alerts',
            'total_incidents',
            'online_devices',
            'uncertainty',
        ]
        read_only_fields = ['owner']

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    invited_by = UserSerializer()
    project = ProjectOverviewSerializer()

    class Meta:
        model = Membership
        fields = '__all__'
        ready_only = ['user']

class ProjectMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=Membership.Role.choices)

class ThreatClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreatClass
        fields = '__all__'

class ProjectThreatClassSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    threat_class_id = serializers.IntegerField(source="threat_class.id")

    class Meta:
        model = ProjectThreatClass
        fields = ["id", "threat_class_id"]
        read_only = ["id"]


@transaction.atomic
def generate_grid(project, cell_size=100):
    # Remove existing cells if we're regenerating
    project.grid_cells.all().delete()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                ST_AsEWKT(
                    ST_Transform(
                        dumped.geom,
                        4326
                    )
                )
            FROM projects_project p

            CROSS JOIN LATERAL
                ST_SquareGrid(
                    %s,
                    ST_Transform(p.monitoring_area, 32647)
                ) AS grid(geom)

            CROSS JOIN LATERAL
                ST_Dump(
                    ST_Intersection(
                        grid.geom,
                        ST_Transform(p.monitoring_area, 32647)
                    )
                ) AS dumped

            WHERE p.id = %s
            AND NOT ST_IsEmpty(dumped.geom)
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
    dem_dir = settings.BASE_DIR / "data" / "dem"
    dem_dir.mkdir(parents=True, exist_ok=True)

    dem_path = dem_dir / f"project_{project.id}_dem.tif"
    slope_path = dem_dir / f"project_{project.id}_slope.tif"

    download_dem(
        project,
        dem_path
    )

    generate_slope_raster(
        dem_path,
        slope_path
    )

    populate_terrain_data(project, dem_path, slope_path)

    # Road data is optional; Overpass availability must not block grid creation.
    try:
        data = download_osm_roads(project)
    except requests.exceptions.RequestException:
        logger.exception(
            "Could not download OSM roads for project %s; "
            "grid generation will continue without road data.",
            project.id,
        )
    else:
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

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class ProjectSerializer(GeoFeatureModelSerializer):
    members = ProjectMemberSerializer(many=True, required=False)
    threat_classes = ProjectThreatClassSerializer(many=True, required=False)

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
                role=member['role'],
                invited_by=project.owner
            )

        # create membership for owner
        Membership.objects.create(
            project=project,
            user=project.owner,
            role=Membership.Role.OWNER,
            accepted=True,
            join_date=timezone.now(),
            invited_by=project.owner
        )

        # record threat classes to detect
        for threat_class in threat_classes:
            ProjectThreatClass.objects.create(
                project=project,
                threat_class=ThreatClass.objects.get(pk=threat_class["threat_class"]["id"])
            )

        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        threat_classes = validated_data.pop("threat_classes", None)
        monitoring_area = validated_data.get("monitoring_area")
        monitoring_area_changed = (
            monitoring_area is not None
            and monitoring_area != instance.monitoring_area
        )

        project = super().update(instance, validated_data)

        if threat_classes is not None:
            project.threat_classes.all().delete()
            for threat_class in threat_classes:
                ProjectThreatClass.objects.create(
                    project=project,
                    threat_class_id=threat_class["id"],
                )

        if monitoring_area_changed:
            generate_grid(project=project, cell_size=100)

        return project


class IncidentSerializer(serializers.ModelSerializer):
    threat_class = ThreatClassSerializer()
    device = DeviceSerializer()
    project = ProjectOverviewSerializer()

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
        fields = ['id', 'user', 'role']

class PatrolProjectNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id','name']

class PatrolSerializer(serializers.ModelSerializer):
    incident = IncidentSerializer()
    project = PatrolProjectNameSerializer()
    assigned_by = PatrolAssignerSerializer()
    members = PatrolAssignerSerializer(many=True, read_only=True)

    class Meta:
        model = Patrol
        fields = '__all__'
        geo_field = 'target'


class RoutinePatrolSerializer(serializers.ModelSerializer):
    project = PatrolProjectNameSerializer(read_only=True)
    created_by = PatrolAssignerSerializer(read_only=True)
    path = GeometryField()

    class Meta:
        model = RoutinePatrol
        fields = [
            "id",
            "project",
            "created_by",
            "name",
            "frequency",
            "start_date",
            "path",
            "created_at",
        ]
        read_only_fields = ["id", "project", "created_by", "created_at"]

    def validate_path(self, value):
        if value.geom_type != "LineString" or len(value.coords) < 2:
            raise serializers.ValidationError(
                "Path must be a LineString with at least two waypoints."
            )
        return value


class DeviceConnectSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)
    coordinate = GeometryField()
    battery = serializers.IntegerField()

    def validate_coordinate(self, value):
        if value.geom_type != "Point":
            raise serializers.ValidationError("Coordinate must be a Point.")
        return value
