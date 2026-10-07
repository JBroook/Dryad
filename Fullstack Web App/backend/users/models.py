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
    verified = models.BooleanField(default=False)
    verification_code_hash = models.CharField(
        max_length=128,
        blank=True,
        null=True,
    )

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