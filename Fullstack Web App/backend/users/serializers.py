from django.contrib.auth import authenticate
from rest_framework import serializers

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