from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            email = attrs["email"],
            password = attrs["password"]
        )

        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        attrs["user"] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password']

        read_only_fields = ['id', 'email']

    def create(self, validated_data):
        password = validated_data.pop["password"]
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user