from rest_framework import serializers
from .models import Project, Membership, ThreatClass, ProjectThreatClass, Incident, Device
from users.models import User
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from django.contrib.gis.geos import GEOSGeometry
import json

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'

class ProjectMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=Membership.Role.choices)

class ProjectThreatClassSerializer(serializers.Serializer):
    id = serializers.IntegerField()

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

        if "monitoring_area" in validated_data:
            geojson = validated_data["monitoring_area"]

            if geojson.get("type") == "Feature":
                geojson = geojson["geometry"]

            validated_data["monitoring_area"] = GEOSGeometry(
                json.dumps(geojson),
                srid=4326
            )

        project = Project.objects.create(**validated_data)

        for member in members:
            Membership.objects.create(
                project=project,
                user=User.objects.get(pk=member["id"]),
                role=member['role']
            )

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