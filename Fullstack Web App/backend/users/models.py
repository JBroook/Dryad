from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

import os
import resend
from dotenv import load_dotenv
from django.template.loader import render_to_string

load_dotenv()

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)


# Create your models here.
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
    )
    verified = models.BooleanField(default=False)
    verification_code_hash = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )

    password_reset_token_hash = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )
    password_reset_token_expires_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    receive_emails = models.BooleanField(default=True)
    receive_invite_emails = models.BooleanField(default=True)
    critical_incidents_only = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    def send_verification_email(self, code):
        resend.api_key = os.getenv("RESEND_API_KEY")

        html = render_to_string(
            "emails/verification_code.html",
            {
                "verification_code": code,
            }
        )

        params: resend.Emails.SendParams = {
            "from": "Dryad <onboarding@resend.dev>",
            "to": [os.getenv("REAL_EMAIL")],# should be self.email, but resend limits to own email only for testing
            "subject": "Dryad: Verification Code",
            "html": html,
        }

        resend.Emails.send(params)

    def send_password_reset_email(self, token):
        resend.api_key = os.getenv("RESEND_API_KEY")

        reset_url = (
            f"{os.getenv('FRONTEND_URL')}"
            f"/login/reset-password?token={token}"
        )

        html = render_to_string(
            "emails/password_reset.html",
            {
                "reset_url": reset_url,
            }
        )

        params: resend.Emails.SendParams = {
            "from": "Dryad <onboarding@resend.dev>",
            "to": [os.getenv("REAL_EMAIL")],
            "subject": "Dryad: Password Reset Request",
            "html": html,
        }

        resend.Emails.send(params)
