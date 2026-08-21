from rest_framework import serializers
from .models import Project, Membership, ThreatClass, ProjectThreatClass
from users.models import User

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'

class ProjectMemberSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=Membership.Role.choices)

class ProjectThreatClassSerializer(serializers.Serializer):
    id = serializers.IntegerField()

class ProjectSerializer(serializers.ModelSerializer):
    members = ProjectMemberSerializer(many=True, required=False)
    threat_classes = ProjectThreatClassSerializer(many=True, required=False)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['owner']

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        threat_classes = validated_data.pop("threat_classes", [])
        project = Project.objects.create(**validated_data)

        print("hello?", validated_data)

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
