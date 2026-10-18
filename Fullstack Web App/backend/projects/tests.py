from django.contrib.gis.geos import Point, Polygon
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import GridCell, Incident, Membership, Patrol, Project, ThreatClass
from users.models import User


class PatrolAssignmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.assigner_user = User.objects.create_user(
            email="assigner@example.com",
            password="test-password",
        )
        self.project = Project.objects.create(
            name="Patrol Test Project",
            region="Test region",
            color="#0055ff",
            owner=self.assigner_user,
            coordinates="0,0",
            surface_area=2500,
            monitoring_area=Polygon.from_bbox((0, 0, 10, 10)),
        )
        self.assigner = Membership.objects.create(
            project=self.project,
            user=self.assigner_user,
            invited_by=self.assigner_user,
            role=Membership.Role.OWNER,
        )
        self.assignees = [
            Membership.objects.create(
                project=self.project,
                user=User.objects.create_user(
                    email=f"member{index}@example.com",
                    password="test-password",
                ),
                invited_by=self.assigner_user,
                role=Membership.Role.VIEWER,
            )
            for index in range(1, 4)
        ]
        grid_cell = GridCell.objects.create(
            project=self.project,
            geometry=Polygon.from_bbox((0, 0, 5, 5)),
            identifier="cell-1",
        )
        threat_class = ThreatClass.objects.create(
            name="Test threat",
            description="A test threat",
        )
        self.incident = Incident.objects.create(
            project=self.project,
            threat_class=threat_class,
            coordinates=Point(1, 1, srid=4326),
            confidence=90,
            grid_cell=grid_cell,
        )

    def test_members_share_one_patrol_and_completion_resolves_it_for_all(self):
        assign_url = reverse("assign_patrol", args=[self.incident.id])
        first_response = self.client.post(
            assign_url,
            {
                "assigner_id": self.assigner.id,
                "assignee_ids": [self.assignees[0].id, self.assignees[1].id],
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {member["id"] for member in first_response.data["members"]},
            {self.assignees[0].id, self.assignees[1].id},
        )

        second_response = self.client.post(
            assign_url,
            {
                "assigner_id": self.assigner.id,
                "assignee_ids": [self.assignees[2].id],
            },
            format="json",
        )

        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.data["id"], first_response.data["id"])
        self.assertEqual(Patrol.objects.filter(incident=self.incident).count(), 1)
        patrol = Patrol.objects.get(incident=self.incident)
        self.assertSetEqual(
            set(patrol.members.values_list("id", flat=True)),
            {member.id for member in self.assignees},
        )

        completion_response = self.client.post(
            reverse("complete_patrol", args=[patrol.id]),
            {
                "patrol_status": Patrol.Status.COMPLETED,
                "incident_status": Incident.Status.CONFIRMED,
            },
            format="json",
        )

        self.assertEqual(completion_response.status_code, status.HTTP_200_OK)
        for member in self.assignees:
            self.assertEqual(
                Patrol.objects.get(members=member).status,
                Patrol.Status.COMPLETED,
            )
