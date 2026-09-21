from datetime import timedelta
from django.utils import timezone

from users.models import User
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

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
    created_at = models.DateTimeField()

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

class Device(models.Model):
    name = models.CharField(max_length=50)
    location = models.PointField()
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)
    battery = models.IntegerField()

    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"

    status = models.CharField(
        choices=Status.choices
    )

    last_seen = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GridCell(models.Model):
    project = models.ForeignKey(
        to=Project,
        on_delete=models.CASCADE,
        related_name="grid_cells"
    )

    risk_score = models.FloatField(default=0)

    geometry = models.PolygonField(
        srid=4326
    )

    identifier = models.CharField(max_length=10)

    elevation = models.FloatField(null=True, blank=True)
    slope = models.FloatField(null=True, blank=True)

    distance_to_road = models.FloatField(null=True, blank=True)

class Incident(models.Model):
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, related_name="incidents")
    threat_class = models.ForeignKey(to=ThreatClass, on_delete=models.CASCADE)
    coordinates = models.PointField()
    timestamp = models.DateTimeField(default=timezone.now)
    confidence = models.IntegerField(validators=[
        MaxValueValidator(100),
        MinValueValidator(0)
    ])
    device = models.ForeignKey(to=Device, on_delete=models.CASCADE, blank=True, null=True)
    grid_cell = models.ForeignKey(to=GridCell, on_delete=models.CASCADE)

    class Status(models.TextChoices):
        UNCONFIRMED = "unconfirmed", "Unconfirmed"
        CONFIRMED = "confirmed", "Confirmed"
        DISMISSED = "dismissed", "Dismissed"

    status = models.CharField(choices=Status.choices, default=Status.UNCONFIRMED)

    def __str__(self):
        return f"{self.project.name}: {self.threat_class.name}"

class Patrol(models.Model):
    target = models.PointField()
    member = models.ForeignKey(to=Membership, on_delete=models.CASCADE)
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)
    incident = models.ForeignKey(to=Incident, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(to=Membership, on_delete=models.CASCADE, related_name="assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Status(models.TextChoices):
            PENDING = "pending", "Pending"
            COMPLETED = "completed", "Completed"
            CANCELLED = "cancelled", "Cancelled"
    
    status = models.CharField(choices=Status.choices, default=Status.PENDING)


class ConnectionCode(models.Model):
    code = models.CharField(max_length=6, unique=True)
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    device = models.ForeignKey(to=Device, on_delete=models.CASCADE, blank=True, null=True)

    @property
    def is_valid(self):
        return (
            self.used_at is None
            and timezone.now() < self.expires_at
        )

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)

class OSMRoad(models.Model):
    osm_id = models.BigIntegerField(unique=True)
    geometry = models.LineStringField(srid=4326)