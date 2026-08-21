from rest_framework import serializers
from .models import Project, Membership

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    members = MembershipSerializer(many=True, required=False)

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['owner']
        extra_kwargs = {
            'threat_classes': {'required': False}
        }

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        project = Project.objects.create(**validated_data)

        for member in members:
            Membership.objects.create(
                project=project,
                **member
            )

        return project
