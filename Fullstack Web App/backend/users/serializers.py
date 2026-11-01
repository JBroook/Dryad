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
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'password',
            'date_joined',
            'profile_picture',
        ]

        read_only_fields = ['id', 'email']

    def validate_profile_picture(self, image):
        if image is not None and image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "Profile pictures must be 5 MB or smaller."
            )
        return image

    def update(self, instance, validated_data):
        old_picture_name = (
            instance.profile_picture.name
            if instance.profile_picture
            else None
        )
        old_picture_storage = instance.profile_picture.storage
        user = super().update(instance, validated_data)
        new_picture_name = (
            user.profile_picture.name
            if user.profile_picture
            else None
        )

        if old_picture_name and old_picture_name != new_picture_name:
            from django.db import transaction

            transaction.on_commit(
                lambda: old_picture_storage.delete(old_picture_name)
            )

        return user

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'receive_emails',
            'receive_invite_emails',
            'critical_incidents_only',
        ]

    def validate(self, attrs):
        if attrs.get("critical_incidents_only") is True:
            attrs["receive_emails"] = True
            attrs["receive_invite_emails"] = False
        elif (
            attrs.get("receive_emails") is False
            or attrs.get("receive_invite_emails") is True
        ):
            attrs["critical_incidents_only"] = False
        elif self.instance.critical_incidents_only:
            attrs["receive_emails"] = True
            attrs["receive_invite_emails"] = False

        return attrs

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