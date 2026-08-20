from rest_framework import serializers
from .models import Project, Membership

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    members = MembershipSerializer(many=True)

    class Meta:
        model = Project
        fields = '__all__'

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        project = Project.objects.create(**validated_data)

        for member in members:
            Membership.objects.create(
                project=project,
                **member
            )
