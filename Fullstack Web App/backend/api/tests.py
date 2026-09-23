from datetime import timedelta

from django.contrib.gis.geos import Point, Polygon
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import ConnectionCode, Device, GridCell, Project
from users.models import User


class DeviceConnectionViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="password123",
            first_name="Owner",
            last_name="User",
        )
        self.project = Project.objects.create(
            name="Test Project",
            status=True,
            region="Test region",
            color="#0055ff",
            owner=self.owner,
            description="A project used in tests.",
            confidence_threshold=75,
            coordinates="0,0",
            surface_area=2500,
            monitoring_area=Polygon.from_bbox((0, 0, 10, 10)),
            created_at=timezone.now(),
        )
        self.grid_cell = GridCell.objects.create(
            project=self.project,
            geometry=Polygon.from_bbox((0, 0, 5, 5)),
            risk_score=0,
            identifier="cell-1",
        )
        self.connection_code = ConnectionCode.objects.create(
            code="ABC123",
            project=self.project,
            expires_at=timezone.now() + timedelta(days=1),
        )

    def test_device_connection_assigns_matching_grid_cell(self):
        response = self.client.post(
            reverse("connect_device"),
            {
                "code": self.connection_code.code,
                "coordinate": {"type": "Point", "coordinates": [1, 1]},
                "battery": 80,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        device = Device.objects.get(pk=response.data["device_id"])
        self.assertEqual(device.grid_cell, self.grid_cell)
        self.assertEqual(device.project, self.project)
        self.assertEqual(device.location, Point(1, 1, srid=4326))
