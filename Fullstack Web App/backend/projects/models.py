from users.models import User
from django.contrib.gis.db import models

# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=50)
    status = models.BooleanField(default=True)
    region = models.CharField(max_length=200)
    color = models.CharField(max_length=7)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    confidence_threshold = models.IntegerField(default=75)
    coordinates = models.CharField(max_length=50)
    surface_area = models.IntegerField()
    monitoring_area = models.PolygonField(
        srid=4326
    )

    class AlertPreference(models.TextChoices):
        ALL = "all", "All"
        MANAGERS_AND_UP = "managers and up", "Managers and Up"
        ADMINS_AND_UP = "admins and up", "Admins and Up"
        OWNER_ONLY = "owner only", "Owner Only"

    alert_recipients = models.CharField(
        choices=AlertPreference.choices,
        default=AlertPreference.ALL
    )

    def __str__(self):
        return self.name

class ThreatClass(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class ProjectThreatClass(models.Model):
    threat_class = models.ForeignKey(to=ThreatClass, on_delete=models.CASCADE)
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, related_name="threat_classes")

    def __str__(self):
        return self.project.name + ": " + self.threat_class.name


class Membership(models.Model):
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    join_date = models.DateField(null=True, blank=True)
    accepted = models.BooleanField(default=False)

    class Role(models.TextChoices):
        VIEWER = "viewer", "Viewer"
        MANAGER = "manager", "Manager"
        ADMIN = "admin", "Admin"
        OWNER = "owner", "Owner"

    role = models.CharField(choices=Role.choices,)

    def __str__(self):
        return self.project.name + ": " + self.user.email