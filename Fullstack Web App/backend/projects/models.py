from django.db import models
from users.models import User

# Create your models here.
class ThreatClasses(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Project(models.Model):
    name = models.CharField(max_length=50)
    status = models.BooleanField(default=True)
    region = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    confidence_threshold = models.IntegerField(default=75)
    coordinates = models.CharField(max_length=50)
    surface_area = models.IntegerField()

    class AlertPreference(models.TextChoices):
        ALL = "all", "All"
        MANAGERS_AND_UP = "managers and up", "Managers and Up"
        ADMINS_AND_UP = "admins and up", "Admins and Up"
        OWNER_ONLY = "owner only", "Owner Only"

    alert_recipients = models.CharField(
        choices=AlertPreference.choices,
        default=AlertPreference.ALL
    )

    threat_classes = models.ManyToManyField(ThreatClasses)

    def __str__(self):
        return self.name

class Membership(models.Model):
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    join_date = models.DateField(null=True)
    accepted = models.BooleanField(default=False)

    class Role(models.TextChoices):
        VIEWER = "viewer", "Viewer"
        MANAGER = "manager", "Manager"
        ADMIN = "admin", "Admin"
        OWNER = "owner", "Owner"

    role = models.CharField(choices=Role.choices,)  