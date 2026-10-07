from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
import secrets
from django.contrib.auth.hashers import make_password

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

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={"input_type" : "password"})

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "first_name",
            "last_name"
        ]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )

        return value

    def validate_password(self, value):
        validate_password(value, self.instance)
        return value

    def create(self, validated_data):
        code = f"{secrets.randbelow(1_000_000):06d}"
        code_hash = make_password(code)

        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.verification_code_hash = code_hash

        user.save()

        user.send_verification_email(code)

        return user

class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(
        min_length=6,
        max_length=6,
    )

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password']

        read_only_fields = ['id', 'email']

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        return attrs