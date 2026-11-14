import os
import tempfile
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from django.contrib.gis.geos import LineString, Point, Polygon
from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from xml.etree import ElementTree
from rest_framework import status
from rest_framework.test import APIClient
import numpy as np
from rasterio.transform import from_origin
from projects.terrain import generate_slope_raster
from projects.terrain import download_dem

from projects.models import (
    ConnectionCode,
    Device,
    GridCell,
    Incident,
    Membership,
    Patrol,
    Project,
    ProjectThreatClass,
    RoutinePatrol,
    ThreatClass,
)
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
            accepted=True,
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
                accepted=True,
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
        self.client.force_authenticate(user=self.assigner_user)

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
        self.assertEqual(first_response.data["message"], "Patrol assigned successfully.")
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
        self.assertEqual(
            completion_response.data["message"],
            "Patrol completed and incident status updated successfully.",
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.confirmed_incidents_since_training, 1)
        for member in self.assignees:
            self.assertEqual(
                Patrol.objects.get(members=member).status,
                Patrol.Status.COMPLETED,
            )

    def test_direct_incident_confirmation_is_counted_once(self):
        response = self.client.patch(
            reverse("incident-detail", args=[self.incident.id]),
            {"status": Incident.Status.CONFIRMED},
            format="json",
        )
        repeated_response = self.client.patch(
            reverse("incident-detail", args=[self.incident.id]),
            {"status": Incident.Status.CONFIRMED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(repeated_response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.confirmed_incidents_since_training, 1)

    def test_project_can_create_routine_patrol_with_route(self):
        self.client.force_authenticate(user=self.assigner_user)
        response = self.client.post(
            reverse("project_routine_patrols", args=[self.project.id]),
            {
                "name": "North boundary",
                "frequency": RoutinePatrol.Frequency.WEEKLY,
                "start_date": "2026-10-20",
                "path": {
                    "type": "LineString",
                    "coordinates": [[1, 2], [3, 4]],
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["message"],
            "Routine Patrol created successfully.",
        )
        routine_patrol = RoutinePatrol.objects.get()
        self.assertEqual(routine_patrol.project, self.project)
        self.assertEqual(routine_patrol.created_by, self.assigner)
        self.assertEqual(routine_patrol.name, "North boundary")
        self.assertEqual(routine_patrol.frequency, RoutinePatrol.Frequency.WEEKLY)
        self.assertEqual(routine_patrol.start_date.isoformat(), "2026-10-20")
        self.assertEqual(routine_patrol.path.geom_type, "LineString")
        self.assertEqual(len(routine_patrol.path.coords), 2)

    def test_routine_patrol_requires_a_route_with_two_waypoints(self):
        self.client.force_authenticate(user=self.assigner_user)
        response = self.client.post(
            reverse("project_routine_patrols", args=[self.project.id]),
            {
                "name": "Incomplete route",
                "frequency": RoutinePatrol.Frequency.DAILY,
                "start_date": "2026-10-20",
                "path": {
                    "type": "LineString",
                    "coordinates": [[1, 2]],
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(RoutinePatrol.objects.exists())

    def test_project_can_list_its_routine_patrols(self):
        self.client.force_authenticate(user=self.assigner_user)
        RoutinePatrol.objects.create(
            project=self.project,
            created_by=self.assigner,
            name="North boundary",
            frequency=RoutinePatrol.Frequency.WEEKLY,
            start_date="2026-10-20",
            path=LineString([(1, 2), (3, 4)], srid=4326),
        )

        response = self.client.get(
            reverse("project_routine_patrols", args=[self.project.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "North boundary")
        self.assertEqual(response.data[0]["created_by"]["id"], self.assigner.id)

    def test_project_member_can_get_routine_patrol_geometry(self):
        self.client.force_authenticate(user=self.assigner_user)
        routine_patrol = RoutinePatrol.objects.create(
            project=self.project,
            created_by=self.assigner,
            name="North boundary",
            frequency=RoutinePatrol.Frequency.WEEKLY,
            start_date="2026-10-20",
            path=LineString([(1, 2), (3, 4)], srid=4326),
        )

        response = self.client.get(
            reverse(
                "project_routine_patrol_detail",
                args=[self.project.id, routine_patrol.id],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["path"]["type"], "LineString")
        self.assertEqual(response.data["path"]["coordinates"], [[1.0, 2.0], [3.0, 4.0]])

    def test_project_manager_can_delete_routine_patrol(self):
        manager_user = User.objects.create_user(
            email="routine-manager@example.com",
            password="test-password",
        )
        Membership.objects.create(
            project=self.project,
            user=manager_user,
            invited_by=self.assigner_user,
            role=Membership.Role.MANAGER,
            accepted=True,
        )
        routine_patrol = RoutinePatrol.objects.create(
            project=self.project,
            created_by=self.assigner,
            name="North boundary",
            frequency=RoutinePatrol.Frequency.WEEKLY,
            start_date="2026-10-20",
            path=LineString([(1, 2), (3, 4)], srid=4326),
        )
        self.client.force_authenticate(user=manager_user)

        response = self.client.delete(
            reverse(
                "project_routine_patrol_detail",
                args=[self.project.id, routine_patrol.id],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "Routine Patrol deleted successfully.",
        )
        self.assertFalse(RoutinePatrol.objects.filter(pk=routine_patrol.id).exists())

    def test_project_viewer_cannot_delete_routine_patrol(self):
        routine_patrol = RoutinePatrol.objects.create(
            project=self.project,
            created_by=self.assigner,
            name="North boundary",
            frequency=RoutinePatrol.Frequency.WEEKLY,
            start_date="2026-10-20",
            path=LineString([(1, 2), (3, 4)], srid=4326),
        )
        viewer_membership = self.assignees[0]
        self.client.force_authenticate(user=viewer_membership.user)

        response = self.client.delete(
            reverse(
                "project_routine_patrol_detail",
                args=[self.project.id, routine_patrol.id],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(RoutinePatrol.objects.filter(pk=routine_patrol.id).exists())

    def test_routine_patrol_gpx_export_returns_track_for_project_member(self):
        self.client.force_authenticate(user=self.assigner_user)
        routine_patrol = RoutinePatrol.objects.create(
            project=self.project,
            created_by=self.assigner,
            name="North & East",
            frequency=RoutinePatrol.Frequency.WEEKLY,
            start_date="2026-10-20",
            path=LineString([(1, 2), (3, 4)], srid=4326),
        )

        response = self.client.get(
            reverse(
                "routine_patrol_gpx_export",
                args=[self.project.id, routine_patrol.id],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/gpx+xml; charset=utf-8")
        self.assertIn(".gpx", response["Content-Disposition"])
        document = ElementTree.fromstring(response.content)
        namespace = {"gpx": "http://www.topografix.com/GPX/1/1"}
        track_name = document.findtext("gpx:trk/gpx:name", namespaces=namespace)
        trackpoints = document.findall(".//gpx:trkpt", namespace)
        self.assertEqual(track_name, "North & East")
        self.assertEqual(len(trackpoints), 2)
        self.assertEqual(trackpoints[0].attrib, {"lat": "2.0000000", "lon": "1.0000000"})

    def test_routine_patrol_gpx_export_is_not_available_to_non_members(self):
        outsider = User.objects.create_user(
            email="outsider@example.com",
            password="test-password-123",
        )
        self.client.force_authenticate(user=outsider)
        routine_patrol = RoutinePatrol.objects.create(
            project=self.project,
            created_by=self.assigner,
            name="North boundary",
            frequency=RoutinePatrol.Frequency.WEEKLY,
            start_date="2026-10-20",
            path=LineString([(1, 2), (3, 4)], srid=4326),
        )

        response = self.client.get(
            reverse(
                "routine_patrol_gpx_export",
                args=[self.project.id, routine_patrol.id],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_list_routine_patrols_from_their_projects(self):
        self.client.force_authenticate(user=self.assigner_user)
        RoutinePatrol.objects.create(
            project=self.project,
            created_by=self.assigner,
            name="North boundary",
            frequency=RoutinePatrol.Frequency.WEEKLY,
            start_date="2026-10-20",
            path=LineString([(1, 2), (3, 4)], srid=4326),
        )

        response = self.client.get(
            reverse("user_routine_patrols", args=[self.assigner_user.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "North boundary")

    def test_generate_routine_patrol_path_uses_very_high_risk_grid_cells(self):
        self.client.force_authenticate(user=self.assigner_user)
        GridCell.objects.filter(pk=self.incident.grid_cell_id).update(
            risk_score=0.95,
            geometry=Polygon.from_bbox((0, 0, 2, 2)),
        )
        GridCell.objects.create(
            project=self.project,
            geometry=Polygon.from_bbox((8, 8, 10, 10)),
            risk_score=0.85,
            identifier="cell-2",
        )
        GridCell.objects.create(
            project=self.project,
            geometry=Polygon.from_bbox((0, 5, 2, 7)),
            risk_score=0.79,
            identifier="cell-3",
        )

        response = self.client.post(
            reverse("generate_routine_patrol_path", args=[self.project.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["path"]["type"], "LineString")
        self.assertEqual(response.data["hotspot_count"], 2)
        self.assertEqual(len(response.data["path"]["coordinates"]), 2)

    def test_generate_routine_patrol_path_requires_two_hotspots(self):
        self.client.force_authenticate(user=self.assigner_user)
        GridCell.objects.filter(pk=self.incident.grid_cell_id).update(risk_score=0.9)

        response = self.client.post(
            reverse("generate_routine_patrol_path", args=[self.project.id])
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_viewer_cannot_assign_patrol_or_edit_incident_directly(self):
        viewer = self.assignees[0]
        self.client.force_authenticate(user=viewer.user)

        assign_response = self.client.post(
            reverse("assign_patrol", args=[self.incident.id]),
            {
                "assigner_id": viewer.id,
                "assignee_ids": [self.assignees[1].id],
            },
            format="json",
        )
        incident_response = self.client.patch(
            reverse("incident-detail", args=[self.incident.id]),
            {"status": Incident.Status.CONFIRMED},
            format="json",
        )

        self.assertEqual(assign_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(incident_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Patrol.objects.exists())

    def test_manager_can_assign_patrols_but_viewer_cannot_manage_devices(self):
        manager_user = User.objects.create_user(
            email="patrol-manager@example.com",
            password="test-password",
        )
        Membership.objects.create(
            project=self.project,
            user=manager_user,
            invited_by=self.assigner_user,
            role=Membership.Role.MANAGER,
            accepted=True,
        )
        self.client.force_authenticate(user=manager_user)
        assign_response = self.client.post(
            reverse("assign_patrol", args=[self.incident.id]),
            {
                "assignee_ids": [self.assignees[0].id],
                "assigner_id": self.assigner.id,
            },
            format="json",
        )

        self.client.force_authenticate(user=self.assignees[0].user)
        device_response = self.client.post(
            reverse("project_devices-list", args=[self.project.id]),
            {},
            format="json",
        )

        self.assertEqual(assign_response.status_code, status.HTTP_200_OK)
        self.assertEqual(device_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_can_only_complete_a_patrol_assigned_to_them(self):
        patrol = Patrol.objects.create(
            project=self.project,
            incident=self.incident,
            target=self.incident.coordinates,
            assigned_by=self.assigner,
        )
        patrol.members.add(self.assignees[0])
        other_patrol = Patrol.objects.create(
            project=self.project,
            incident=self.incident,
            target=self.incident.coordinates,
            assigned_by=self.assigner,
        )
        other_patrol.members.add(self.assignees[1])
        cancelled_patrol = Patrol.objects.create(
            project=self.project,
            incident=self.incident,
            target=self.incident.coordinates,
            assigned_by=self.assigner,
        )
        cancelled_patrol.members.add(self.assignees[0])

        self.client.force_authenticate(user=self.assignees[0].user)
        response = self.client.post(
            reverse("complete_patrol", args=[patrol.id]),
            {
                "patrol_status": Patrol.Status.COMPLETED,
                "incident_status": Incident.Status.CONFIRMED,
            },
            format="json",
        )
        forbidden_response = self.client.post(
            reverse("complete_patrol", args=[other_patrol.id]),
            {
                "patrol_status": Patrol.Status.COMPLETED,
                "incident_status": Incident.Status.DISMISSED,
            },
            format="json",
        )
        cancel_response = self.client.post(
            reverse("complete_patrol", args=[cancelled_patrol.id]),
            {"patrol_status": Patrol.Status.CANCELLED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Patrol.objects.get(pk=patrol.pk).status,
            Patrol.Status.COMPLETED,
        )
        self.assertEqual(
            Patrol.objects.get(pk=other_patrol.pk).status,
            Patrol.Status.PENDING,
        )
        self.assertFalse(Patrol.objects.filter(pk=cancelled_patrol.pk).exists())

    def test_manager_can_invite_but_not_change_project_settings_or_elevate(self):
        manager_user = User.objects.create_user(
            email="manager@example.com",
            password="test-password",
        )

        invited_user = User.objects.create_user(
            email="new-member@example.com",
            password="test-password",
        )

        Membership.objects.create(
            project=self.project,
            user=manager_user,
            invited_by=self.assigner_user,
            role=Membership.Role.MANAGER,
            accepted=True,
        )

        self.client.force_authenticate(user=manager_user)

        settings_response = self.client.patch(
            reverse("project-detail", args=[self.project.id]),
            {"name": "Changed by manager"},
            format="json",
        )

        role_response = self.client.patch(
            reverse("member-detail", args=[self.project.id, self.assignees[2].id]),
            {"role": Membership.Role.ADMIN},
            format="json",
        )

        with patch("api.views.resend.Emails.send"):
            invite_response = self.client.post(
                reverse("invite", args=[self.project.id]) + "?email=new-member@example.com",
            )

        self.assertEqual(
            settings_response.status_code,
            status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            role_response.status_code,
            status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            invite_response.status_code,
            status.HTTP_201_CREATED
        )

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Patrol Test Project")

        self.assertTrue(
            Membership.objects.filter(
                project=self.project,
                user=invited_user,
                role=Membership.Role.VIEWER,
            ).exists()
        )

    def test_admin_can_edit_settings_but_cannot_disable_project(self):
        admin_user = User.objects.create_user(
            email="admin@example.com",
            password="test-password",
        )
        Membership.objects.create(
            project=self.project,
            user=admin_user,
            invited_by=self.assigner_user,
            role=Membership.Role.ADMIN,
            accepted=True,
        )
        self.client.force_authenticate(user=admin_user)

        update_response = self.client.patch(
            reverse("project-detail", args=[self.project.id]),
            {"name": "Changed by admin"},
            format="json",
        )
        User.objects.create_user(
            email="invited-by-admin@example.com",
            password="test-password",
        )
        invite_response = self.client.post(
            f"{reverse('invite', args=[self.project.id])}?email=invited-by-admin@example.com"
        )
        disable_response = self.client.patch(
            reverse("project-detail", args=[self.project.id]),
            {"status": False},
            format="json",
        )
        delete_response = self.client.delete(
            reverse("project-detail", args=[self.project.id])
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(invite_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(disable_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Changed by admin")
        self.assertTrue(self.project.status)


class AuthenticationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_data = {
            "email": "new-user@example.com",
            "password": "Testpass123!",
            "first_name": "New",
            "last_name": "User",
        }

    @patch("users.models.User.send_verification_email")
    def test_registration_creates_user_with_hashed_verification_code(self, send_email):
        response = self.client.post(
            reverse("register"),
            self.register_data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=self.register_data["email"])
        self.assertTrue(user.check_password(self.register_data["password"]))
        self.assertIsNotNone(user.verification_code_hash)
        self.assertFalse(user.verified)
        code = send_email.call_args.args[0]
        self.assertTrue(check_password(code, user.verification_code_hash))

    def test_registration_rejects_an_existing_email_case_insensitively(self):
        User.objects.create_user(
            email=self.register_data["email"],
            password="Testpass123!",
        )
        data = {**self.register_data, "email": self.register_data["email"].upper()}

        response = self.client.post(reverse("register"), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(email__iexact=data["email"]).count(), 1)

    def test_login_returns_tokens_and_user_for_valid_credentials(self):
        user = User.objects.create_user(
            email="login@example.com",
            verified=True,
            password="Testpass123!",
        )

        response = self.client.post(
            reverse("login"),
            {"email": user.email, "password": "Testpass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], user.email)

    def test_login_rejects_an_unverified_user(self):
        user = User.objects.create_user(
            email="unverified@example.com",
            password="Testpass123!",
        )

        response = self.client.post(
            reverse("login"),
            {"email": user.email, "password": "Testpass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "email_not_verified")
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_rejects_an_incorrect_password(self):
        user = User.objects.create_user(
            email="login@example.com",
            password="Testpass123!",
        )

        response = self.client.post(
            reverse("login"),
            {"email": user.email, "password": "Wrongpass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_verification_accepts_the_matching_code_and_clears_hash(self):
        user = User.objects.create_user(
            email="verify@example.com",
            password="Testpass123!",
            verification_code_hash=make_password("004321"),
        )

        response = self.client.post(
            reverse("verify_email"),
            {"email": user.email, "code": "004321"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.verified)
        self.assertIsNone(user.verification_code_hash)

    def test_email_verification_rejects_a_nonmatching_code(self):
        user = User.objects.create_user(
            email="verify@example.com",
            password="Testpass123!",
            verification_code_hash=make_password("004321"),
        )

        response = self.client.post(
            reverse("verify_email"),
            {"email": user.email, "code": "999999"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertFalse(user.verified)

    def test_registration_rejects_a_weak_password(self):
        data = {**self.register_data, "password": "123"}

        response = self.client.post(
            reverse("register"),
            data,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            User.objects.filter(email=data["email"]).exists()
        )


class ProjectAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="project-owner@example.com",  password="Testpass123!",
        )
        self.project = Project.objects.create(
            name="API Test Project", region="Test region", color="#0055ff",
            owner=self.owner, coordinates="0,0", surface_area=1200,
            monitoring_area=Polygon.from_bbox((0, 0, 10, 10)),
        )
        self.owner_membership = Membership.objects.create(
            project=self.project, user=self.owner, invited_by=self.owner,
            role=Membership.Role.OWNER, accepted=True,
        )
        self.cell = GridCell.objects.create(
            project=self.project, geometry=Polygon.from_bbox((0, 0, 5, 5)),
            identifier="test-cell", elevation=100,
            slope=5, distance_to_road=10,
        )
        self.threat_class = ThreatClass.objects.create(
            name="Test fire",
            description="Fire threat used in tests",
        )
        self.client.force_authenticate(user=self.owner)


class ManualIncidentReportTests(ProjectAPITestCase):
    def setUp(self):
        super().setUp()
        ProjectThreatClass.objects.create(
            project=self.project,
            threat_class=self.threat_class,
        )

    def test_project_manager_can_create_a_manual_incident_report(self):
        timestamp = timezone.now().isoformat()
        response = self.client.post(
            reverse("manual_incident_report", args=[self.project.id]),
            {
                "threat_class": self.threat_class.id,
                "timestamp": timestamp,
                "latitude": 2,
                "longitude": 3,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        incident = Incident.objects.get()
        self.assertEqual(incident.project, self.project)
        self.assertEqual(incident.threat_class, self.threat_class)
        self.assertEqual(incident.coordinates.x, 3)
        self.assertEqual(incident.coordinates.y, 2)
        self.assertEqual(incident.confidence, 100)
        self.assertIsNone(incident.device)
        self.assertTrue(incident.manual_report)
        self.assertEqual(incident.grid_cell, self.cell)
        self.assertTrue(response.data["manual_report"])
        self.assertIsNone(response.data["device"])

    def test_manual_report_requires_a_project_threat_class(self):
        other_threat = ThreatClass.objects.create(
            name="Unconfigured threat",
            description="Not configured for this project",
        )
        response = self.client.post(
            reverse("manual_incident_report", args=[self.project.id]),
            {
                "threat_class": other_threat.id,
                "timestamp": timezone.now().isoformat(),
                "latitude": 2,
                "longitude": 3,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Incident.objects.exists())

    def test_manual_report_location_must_match_a_project_grid_cell(self):
        response = self.client.post(
            reverse("manual_incident_report", args=[self.project.id]),
            {
                "threat_class": self.threat_class.id,
                "timestamp": timezone.now().isoformat(),
                "latitude": 8,
                "longitude": 8,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Incident.objects.exists())

    def test_manual_report_accepts_unambiguously_reversed_coordinates(self):
        GridCell.objects.create(
            project=self.project,
            geometry=Polygon.from_bbox((99, 1, 101, 3)),
            identifier="reverse",
        )

        response = self.client.post(
            reverse("manual_incident_report", args=[self.project.id]),
            {
                "threat_class": self.threat_class.id,
                "timestamp": timezone.now().isoformat(),
                "latitude": 100,
                "longitude": 2,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        incident = Incident.objects.get()
        self.assertEqual(incident.coordinates.x, 100)
        self.assertEqual(incident.coordinates.y, 2)


class ProjectManagementTests(ProjectAPITestCase):
    def test_project_list_only_contains_projects_the_user_owns_or_joined(self):
        outsider = User.objects.create_user(
            email="unrelated-owner@example.com",
            password="Testpass123!",
        )
        Project.objects.create(
            name="Unrelated project",
            region="Elsewhere",
            color="#0055ff",
            owner=outsider,
            coordinates="1,1",
            surface_area=100,
            monitoring_area=Polygon.from_bbox((1, 1, 2, 2)),
        )

        response = self.client.get(reverse("project-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["type"], "FeatureCollection")
        self.assertEqual(
            [feature["id"] for feature in response.data["features"]],
            [self.project.id],
        )

    def test_project_creation_assigns_owner_and_creates_owner_membership(self):
        data = {
            "name": "New project",
            "region": "North",
            "color": "#123456",
            "coordinates": "2,2",
            "surface_area": 500,
            "monitoring_area": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]],
            },
        }

        with (
            patch("projects.serializers.generate_grid") as generate_grid,
            patch("projects.BNN.initialize_project_model") as initialize_model,
            patch("projects.BNN.calculate_project_risk") as calculate_risk,
        ):
            response = self.client.post(
                reverse("project-list"),
                data,
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(name="New project")
        self.assertEqual(project.owner, self.owner)
        self.assertTrue(
            Membership.objects.filter(
                project=project,
                user=self.owner,
                accepted=True,
                role=Membership.Role.OWNER,
            ).exists()
        )
        generate_grid.assert_called_once()
        initialize_model.assert_called_once_with(project)
        calculate_risk.assert_called_once_with(project)

    def test_project_owner_can_update_project_preferences(self):
        response = self.client.patch(
            reverse("project-detail", args=[self.project.id]),
            {
                "name": "Updated project",
                "alert_recipients": Project.AlertPreference.OWNER_ONLY,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated project")
        self.assertEqual(
            self.project.alert_recipients,
            Project.AlertPreference.OWNER_ONLY,
        )

    def test_project_owner_can_disable_and_activate_project(self):
        project_url = reverse("project-detail", args=[self.project.id])

        disable_response = self.client.patch(
            project_url,
            {"status": False},
            format="json",
        )

        self.assertEqual(disable_response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertFalse(self.project.status)

        overview_response = self.client.get(reverse("project_overview"))
        self.assertEqual(overview_response.status_code, status.HTTP_200_OK)
        project_data = next(
            project for project in overview_response.data if project["id"] == self.project.id
        )
        self.assertFalse(project_data["status"])

        activate_response = self.client.patch(
            project_url,
            {"status": True},
            format="json",
        )

        self.assertEqual(activate_response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertTrue(self.project.status)

    def test_project_owner_can_delete_project_and_related_data(self):
        connection_code = ConnectionCode.objects.create(
            code="ABC123",
            project=self.project,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        response = self.client.delete(
            reverse("project-detail", args=[self.project.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Project deleted successfully.")
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())
        self.assertFalse(
            Membership.objects.filter(pk=self.owner_membership.id).exists()
        )
        self.assertFalse(GridCell.objects.filter(pk=self.cell.id).exists())
        self.assertFalse(ConnectionCode.objects.filter(pk=connection_code.id).exists())

    def test_project_settings_are_not_visible_to_an_unrelated_user(self):
        outsider = User.objects.create_user(
            email="project-outsider@example.com",
            password="Testpass123!",
        )
        self.client.force_authenticate(user=outsider)

        response = self.client.get(
            reverse("project-detail", args=[self.project.id])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_project_admin_can_invite_an_existing_user(self):
        admin_user = User.objects.create_user(
            email="project-admin@example.com",
            password="Testpass123!",
        )
        Membership.objects.create(
            project=self.project,
            user=admin_user,
            invited_by=self.owner,
            role=Membership.Role.ADMIN,
            accepted=True,
        )
        invited_user = User.objects.create_user(
            email="invited@example.com",
            password="Testpass123!",
        )
        self.client.force_authenticate(user=admin_user)

        with (
            patch.dict(
                os.environ,
                {
                    "REAL_EMAIL": "test-inbox@example.com",
                    "RESEND_API_KEY": "test-api-key",
                    "FRONTEND_URL": "https://dryad.example.com/",
                },
            ),
            patch("api.views.resend.Emails.send") as send_email,
        ):
            response = self.client.post(
                f"{reverse('invite', args=[self.project.id])}?email={invited_user.email}"
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invitation = Membership.objects.get(
            project=self.project,
            user=invited_user,
        )
        self.assertFalse(invitation.accepted)
        self.assertEqual(invitation.role, Membership.Role.VIEWER)
        send_email.assert_called_once()
        email_params = send_email.call_args.args[0]
        self.assertEqual(email_params["to"], ["test-inbox@example.com"])
        self.assertEqual(email_params["subject"], f"{self.project.name}: Project Invitation")
        self.assertIn(f"You're Invited to {self.project.name}!", email_params["html"])
        self.assertIn("project-admin@example.com", email_params["html"])
        self.assertIn("https://dryad.example.com/home/projects", email_params["html"])

    def test_project_invitation_respects_member_email_preference(self):
        invited_user = User.objects.create_user(
            email="no-invite-email@example.com",
            password="test-password",
            receive_invite_emails=False,
        )

        with patch("api.views.resend.Emails.send") as send_email:
            response = self.client.post(
                f"{reverse('invite', args=[self.project.id])}?email={invited_user.email}"
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Membership.objects.filter(
                project=self.project,
                user=invited_user,
                accepted=False,
            ).exists()
        )
        send_email.assert_not_called()

    def test_project_invitation_requires_an_email_address(self):
        response = self.client.post(reverse("invite", args=[self.project.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["details"], "Email address is required")


class GridGenerationTests(ProjectAPITestCase):
    def generate_grid_with_mocked_integrations(
        self,
        rows,
        cell_size=100,
        download_roads_side_effect=None,
    ):
        from projects.serializers import generate_grid

        cursor = MagicMock()
        cursor.fetchall.return_value = rows
        cursor_context = MagicMock()
        cursor_context.__enter__.return_value = cursor
        bulk_create = MagicMock()
        with (
            patch(
                "projects.serializers.connection",
                SimpleNamespace(cursor=MagicMock(return_value=cursor_context)),
            ),
            patch("projects.serializers.GridCell.objects.bulk_create", bulk_create),
            patch("projects.serializers.download_dem") as download_dem,
            patch("projects.serializers.generate_slope_raster") as generate_slope,
            patch("projects.serializers.populate_terrain_data") as populate_terrain,
            patch(
                "projects.serializers.download_osm_roads",
                return_value={"elements": []},
                side_effect=download_roads_side_effect,
            ) as download_roads,
            patch("projects.serializers.save_osm_roads") as save_roads,
            patch("projects.serializers.populate_road_distances") as populate_distances,
        ):
            generate_grid(self.project, cell_size=cell_size)

        return {
            "cursor": cursor,
            "bulk_create": bulk_create,
            "download_dem": download_dem,
            "generate_slope": generate_slope,
            "populate_terrain": populate_terrain,
            "download_roads": download_roads,
            "save_roads": save_roads,
            "populate_distances": populate_distances,
        }

    @staticmethod
    def ewkt_polygon(x):
        return (
            "SRID=4326;POLYGON (("
            f"{x} 0, {x + 1} 0, {x + 1} 1, {x} 1, {x} 0))"
        )

    def test_grid_generation_builds_cells_with_stable_identifiers(self):
        result = self.generate_grid_with_mocked_integrations(
            [(self.ewkt_polygon(0),), (self.ewkt_polygon(2),)]
        )

        cells = result["bulk_create"].call_args.args[0]
        self.assertEqual([cell.identifier for cell in cells], ["cell-0", "cell-1"])
        self.assertTrue(all(cell.project == self.project for cell in cells))
        self.assertTrue(all(cell.geometry.geom_type == "Polygon" for cell in cells))
        self.assertTrue(all(0 <= cell.risk_score <= 1 for cell in cells))

    def test_grid_generation_uses_the_requested_cell_size_and_project_id(self):
        result = self.generate_grid_with_mocked_integrations(
            [(self.ewkt_polygon(0),)],
            cell_size=250,
        )

        self.assertEqual(
            result["cursor"].execute.call_args.args[1],
            [250, self.project.id],
        )

    def test_grid_generation_removes_existing_cells_before_replacement(self):
        GridCell.objects.create(
            project=self.project,
            geometry=Polygon.from_bbox((0, 0, 1, 1)),
            identifier="old-cell",
        )

        self.generate_grid_with_mocked_integrations(
            [(self.ewkt_polygon(3),)]
        )

        self.assertFalse(
            GridCell.objects.filter(project=self.project, identifier="old-cell").exists()
        )

    def test_grid_generation_runs_terrain_and_road_enrichment(self):
        result = self.generate_grid_with_mocked_integrations(
            [(self.ewkt_polygon(0),)]
        )

        result["download_dem"].assert_called_once()
        result["generate_slope"].assert_called_once()
        result["populate_terrain"].assert_called_once()
        result["download_roads"].assert_called_once_with(self.project)
        result["save_roads"].assert_called_once_with({"elements": []})
        result["populate_distances"].assert_called_once_with(self.project)

    def test_grid_generation_continues_when_road_download_fails(self):
        import requests

        result = self.generate_grid_with_mocked_integrations(
            [(self.ewkt_polygon(0),)],
            download_roads_side_effect=requests.exceptions.ConnectionError(
                "Network is unreachable"
            ),
        )

        result["bulk_create"].assert_called_once()
        result["populate_terrain"].assert_called_once()
        result["download_roads"].assert_called_once_with(self.project)
        result["save_roads"].assert_not_called()
        result["populate_distances"].assert_not_called()

    def test_grid_generation_handles_an_empty_grid_query(self):
        result = self.generate_grid_with_mocked_integrations([])

        result["bulk_create"].assert_called_once_with([], ignore_conflicts=True)
        self.assertFalse(GridCell.objects.filter(project=self.project).exists())
        result["download_dem"].assert_called_once()


class DeviceManagementTests(ProjectAPITestCase):
    def create_connection_code(self, code="ABC123"):
        return ConnectionCode.objects.create(
            code=code,
            project=self.project,
            expires_at=timezone.now() + timedelta(minutes=5),
        )

    def connect_device(self, code, coordinate=None):
        return self.client.post(
            reverse("connect_device"),
            {
                "code": code,
                "coordinate": {
                    "type": "Point",
                    "coordinates": coordinate or [1, 1],
                },
                "battery": 85,
            },
            format="json",
        )

    def test_valid_connection_code_registers_device_and_claims_code(self):
        connection_code = self.create_connection_code()
        ProjectThreatClass.objects.create(
            project=self.project,
            threat_class=self.threat_class,
        )

        response = self.connect_device(connection_code.code)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        device = Device.objects.get(pk=response.data["device_id"])
        connection_code.refresh_from_db()
        self.assertEqual(device.project, self.project)
        self.assertEqual(device.grid_cell, self.cell)
        self.assertEqual(device.battery, 85)
        self.assertEqual(device.status, Device.Status.ONLINE)
        self.assertEqual(connection_code.device, device)
        self.assertIsNotNone(connection_code.used_at)
        self.assertEqual(response.data["threat_classes"], [self.threat_class.id])

    def test_unknown_connection_code_is_rejected(self):
        response = self.connect_device("NOPE00")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid Connection Code")
        self.assertFalse(Device.objects.exists())

    def test_expired_connection_code_cannot_register_a_device(self):
        connection_code = self.create_connection_code("OLD123")
        ConnectionCode.objects.filter(pk=connection_code.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )

        response = self.connect_device(connection_code.code)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Device.objects.exists())

    def test_already_used_connection_code_cannot_register_another_device(self):
        connection_code = self.create_connection_code("USED12")
        ConnectionCode.objects.filter(pk=connection_code.pk).update(
            used_at=timezone.now()
        )

        response = self.connect_device(connection_code.code)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Device.objects.exists())

    def test_device_location_must_be_covered_by_a_project_grid_cell(self):
        connection_code = self.create_connection_code("OUT123")

        response = self.connect_device(connection_code.code, [20, 20])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "No grid cell matches this device location.",
        )
        self.assertFalse(Device.objects.exists())

    def test_viewer_cannot_create_devices_through_project_management_api(self):
        viewer = User.objects.create_user(
            email="device-viewer@example.com",
            password="Testpass123!",
        )
        Membership.objects.create(
            project=self.project,
            user=viewer,
            invited_by=self.owner,
            role=Membership.Role.VIEWER,
            accepted=True,
        )
        self.client.force_authenticate(user=viewer)

        response = self.client.post(
            reverse("project_devices-list", args=[self.project.id]),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Device.objects.exists())


class RiskModelTests(ProjectAPITestCase):
    def test_tenth_confirmed_incident_resets_counter_and_triggers_retraining(self):
        from projects.BNN import record_confirmed_incident

        with (
            patch("projects.BNN.retrain_project_model") as retrain_project_model,
            self.captureOnCommitCallbacks(execute=True) as callbacks,
        ):
            for _ in range(9):
                record_confirmed_incident(self.project.pk)

            self.project.refresh_from_db()
            self.assertEqual(
                self.project.confirmed_incidents_since_training,
                9,
            )
            retrain_project_model.assert_not_called()

            record_confirmed_incident(self.project.pk)

        self.project.refresh_from_db()
        self.assertEqual(self.project.confirmed_incidents_since_training, 0)
        self.assertEqual(len(callbacks), 1)
        retrain_project_model.assert_called_once()

    def test_cyclical_features_repeat_at_their_period(self):
        from projects.BNN import cyclical

        self.assertAlmostEqual(cyclical(0, 24)[0], cyclical(24, 24)[0])
        self.assertAlmostEqual(cyclical(0, 24)[1], cyclical(24, 24)[1])
        self.assertAlmostEqual(cyclical(6, 24)[0], 1.0)

    def test_attack_history_counts_only_the_defined_lookback_windows(self):
        from projects.BNN import get_attack_history_from_memory

        observed_at = timezone.now()
        timestamps = [
            observed_at - timedelta(days=31),
            observed_at - timedelta(days=6),
            observed_at - timedelta(hours=12),
            observed_at + timedelta(hours=1),
        ]

        history = get_attack_history_from_memory(timestamps, observed_at)

        self.assertEqual(history["attacks_last_24h"], 1)
        self.assertEqual(history["attacks_last_7d"], 2)
        self.assertEqual(history["attacks_last_30d"], 2)
        self.assertAlmostEqual(history["days_since_last_attack"], 0.5, places=3)

    def test_future_attack_target_includes_the_seven_day_boundary(self):
        from projects.BNN import get_future_attack_target_from_memory

        observed_at = timezone.now()

        self.assertEqual(
            get_future_attack_target_from_memory(
                [observed_at + timedelta(days=7)],
                observed_at,
            ),
            1,
        )
        self.assertEqual(
            get_future_attack_target_from_memory(
                [observed_at + timedelta(days=7, seconds=1)],
                observed_at,
            ),
            0,
        )

    def test_training_sample_combines_cell_features_and_incident_history(self):
        from projects.BNN import build_training_sample

        observed_at = timezone.now().replace(hour=8)
        sample = build_training_sample(
            self.cell,
            observed_at,
            [observed_at - timedelta(hours=2), observed_at + timedelta(days=1)],
        )

        self.assertEqual(sample["elevation"], 100)
        self.assertEqual(sample["slope"], 5)
        self.assertEqual(sample["distance_to_road"], 10)
        self.assertEqual(sample["attacks_last_24h"], 1)
        self.assertEqual(sample["attacks_last_7d"], 1)
        self.assertEqual(sample["attacks_last_30d"], 1)
        self.assertEqual(sample["days_since_last_attack"], 2 / 24)
        self.assertIn("hour_sin", sample)
        self.assertIn("hour_cos", sample)
        self.assertIn("day_sin", sample)
        self.assertIn("day_cos", sample)
        self.assertEqual(sample["target"], 1)
        self.assertEqual(sample["grid_cell_id"], self.cell.id)

    def test_undersampling_keeps_positive_samples_and_caps_negative_samples(self):
        from projects.BNN import undersample

        samples = [
            {"target": 1, "id": "positive-1"},
            {"target": 1, "id": "positive-2"},
            *[{"target": 0, "id": f"negative-{i}"} for i in range(10)],
        ]

        selected = undersample(samples, negative_ratio=2, seed=7)

        self.assertEqual(sum(sample["target"] == 1 for sample in selected), 2)
        self.assertEqual(sum(sample["target"] == 0 for sample in selected), 4)
        self.assertEqual(
            {sample["id"] for sample in selected if sample["target"] == 1},
            {"positive-1", "positive-2"},
        )

    def test_tensor_conversion_uses_all_model_features_and_targets(self):
        from projects.BNN import FEATURES, samples_to_tensors

        feature_values = {
            feature: index + 1
            for index, feature in enumerate(FEATURES)
        }
        sample = {
            **feature_values,
            "target": 1,
            "timestamp": timezone.now(),
            "grid_cell_id": self.cell.id,
        }

        features, targets = samples_to_tensors([sample])

        self.assertEqual(tuple(features.shape), (1, len(FEATURES)))
        self.assertEqual(tuple(targets.shape), (1,))
        self.assertEqual(features.tolist(), [[float(i + 1) for i in range(len(FEATURES))]])
        self.assertEqual(targets.tolist(), [1.0])

    def test_risk_calculation_stores_model_probabilities_on_each_cell(self):
        import torch
        from projects.BNN import FEATURES, calculate_project_risk

        second_cell = GridCell.objects.create(
            project=self.project,
            geometry=Polygon.from_bbox((5, 5, 10, 10)),
            identifier="cell-2",
            elevation=120,
            slope=8,
            distance_to_road=20,
        )
        model = MagicMock()
        model.return_value = {
            "probabilities": torch.tensor([0.5, 0.880797]),
        }
        scaler = MagicMock()
        scaler.transform.side_effect = lambda values: values

        with patch(
            "projects.BNN.load_project_model",
            return_value=(model, scaler),
        ):
            calculated_cells = calculate_project_risk(self.project)

        self.cell.refresh_from_db()
        second_cell.refresh_from_db()
        self.assertEqual(len(calculated_cells), 2)
        self.assertAlmostEqual(self.cell.risk_score, 0.5, places=5)
        self.assertAlmostEqual(second_cell.risk_score, 0.880797, places=5)
        self.assertEqual(
            len(scaler.transform.call_args.args[0][0]),
            len(FEATURES),
        )

    def test_risk_calculation_includes_attack_history_and_time_features(self):
        import torch
        from projects.BNN import (
            FEATURES,
            build_feature_values,
            calculate_project_risk,
        )

        observed_at = timezone.now()
        incident_time = observed_at - timedelta(hours=2)
        model = MagicMock()
        model.return_value = {
            "probabilities": torch.tensor([0.5]),
        }
        scaler = MagicMock()
        scaler.transform.side_effect = lambda values: values

        with (
            patch(
                "projects.BNN.timezone.now",
                return_value=observed_at,
            ),
            patch(
                "projects.BNN.load_incidents",
                return_value=[
                    {
                        "grid_cell_id": self.cell.id,
                        "timestamp": incident_time,
                    },
                ],
            ),
            patch(
                "projects.BNN.load_project_model",
                return_value=(model, scaler),
            ),
        ):
            calculate_project_risk(self.project)

        expected_features = build_feature_values(
            self.cell,
            observed_at,
            [incident_time],
        )
        self.assertEqual(
            scaler.transform.call_args.args[0][0],
            [expected_features[feature] for feature in FEATURES],
        )

    def test_risk_calculation_stores_average_variance_from_repeated_inference(self):
        import torch
        from projects.BNN import calculate_project_risk

        second_cell = GridCell.objects.create(
            project=self.project,
            geometry=Polygon.from_bbox((5, 5, 10, 10)),
            identifier="cell-2",
            elevation=120,
            slope=8,
            distance_to_road=20,
        )
        model = MagicMock()
        model.side_effect = [
            {"probabilities": torch.tensor([0.5, 0.880797])},
            {"probabilities": torch.tensor([0.880797, 0.5])},
        ]
        scaler = MagicMock()
        scaler.transform.side_effect = lambda values: values

        with (
            patch("projects.BNN.RISK_INFERENCE_PASSES", 2),
            patch(
                "projects.BNN.load_project_model",
                return_value=(model, scaler),
            ),
        ):
            calculate_project_risk(self.project)

        self.cell.refresh_from_db()
        second_cell.refresh_from_db()
        self.project.refresh_from_db()

        expected_mean = (
            torch.sigmoid(torch.tensor(0.0))
            + torch.sigmoid(torch.tensor(2.0))
        ).item() / 2
        expected_variance = torch.var(
            torch.sigmoid(torch.tensor([0.0, 2.0])),
            unbiased=False,
        ).item()
        self.assertAlmostEqual(self.cell.risk_score, expected_mean, places=5)
        self.assertAlmostEqual(second_cell.risk_score, expected_mean, places=5)
        self.assertAlmostEqual(self.project.uncertainty, expected_variance, places=5)

    def test_project_models_are_saved_in_distinct_project_paths(self):
        import torch
        from sklearn.preprocessing import StandardScaler
        from projects.BNN import (
            FEATURES,
            RiskPredictorMCDropout,
            initialize_project_model,
            load_project_model,
            project_model_paths,
        )

        model = RiskPredictorMCDropout(
            num_input_features=len(FEATURES)
        )
        scaler = StandardScaler()
        second_project = SimpleNamespace(pk=self.project.pk + 1)
        self.assertNotEqual(
            project_model_paths(self.project),
            project_model_paths(second_project),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "risk_model.pt"
            scaler_path = Path(temp_dir) / "risk_scaler.pkl"
            with (
                patch(
                    "projects.BNN.project_model_paths",
                    return_value=(model_path, scaler_path),
                ),
                patch(
                    "projects.BNN.torch.load",
                    return_value=model.state_dict(),
                ) as load_checkpoint,
                patch(
                    "projects.BNN.joblib.load",
                    return_value=scaler,
                ) as load_scaler,
            ):
                initialize_project_model(self.project)
                loaded_model, loaded_scaler = load_project_model(self.project)

            self.assertTrue(model_path.is_file())
            self.assertTrue(scaler_path.is_file())
            self.assertEqual(
                set(torch.load(model_path, map_location="cpu")),
                set(model.state_dict()),
            )
            self.assertEqual(
                load_checkpoint.call_args_list[-1].args[0],
                model_path,
            )
            self.assertEqual(load_scaler.call_args_list[-1].args[0], scaler_path)
            self.assertIsNot(loaded_model, model)
            self.assertIs(loaded_scaler, scaler)

    def test_risk_calculation_endpoint_returns_project_uncertainty(self):
        def set_uncertainty(project):
            project.uncertainty = 0.125

        with patch(
            "projects.BNN.calculate_project_risk",
            side_effect=set_uncertainty,
        ):
            response = self.client.post(
                reverse("calculate_risk", args=[self.project.id]),
            )

        self.project.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["uncertainty"], 0.125)
        self.assertEqual(self.project.uncertainty, 0.125)

    def test_risk_model_uses_dropout_without_changing_weights(self):
        import torch
        from projects.BNN import RiskPredictorMCDropout

        model = RiskPredictorMCDropout(num_input_features=1)
        inputs = torch.ones((64, 1))
        original_weights = {
            name: parameter.clone()
            for name, parameter in model.named_parameters()
        }
        outputs = torch.stack(
            [model(inputs)["probabilities"] for _ in range(10)]
        )

        self.assertGreater(torch.unique(outputs).numel(), 1)
        for name, parameter in model.named_parameters():
            self.assertTrue(torch.equal(parameter, original_weights[name]))


class TerrainDataTests(ProjectAPITestCase):
    def test_project_bbox_uses_monitoring_area_extent(self):
        from projects.terrain import get_project_bbox

        self.assertEqual(
            get_project_bbox(self.project),
            {"west": 0.0, "south": 0.0, "east": 10.0, "north": 10.0},
        )

    def test_dem_download_sends_bbox_and_writes_the_response_body(self):
        response = MagicMock(content=b"raster bytes")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "dem.tif"
            with (
                patch("projects.terrain.requests.get", return_value=response) as get,
                patch.dict(os.environ, {"OPENTOPOGRAPHY_KEY": "test-key"}),
            ):
                download_dem(self.project, output_path)

            self.assertEqual(output_path.read_bytes(), b"raster bytes")

        response.raise_for_status.assert_called_once()
        self.assertEqual(get.call_args.args[0], "https://portal.opentopography.org/API/globaldem")
        self.assertEqual(
            get.call_args.kwargs["params"],
            {
                "demtype": "COP30",
                "south": 0.0,
                "north": 10.0,
                "west": 0.0,
                "east": 10.0,
                "outputFormat": "GTiff",
                "API_Key": "test-key",
            },
        )

    def test_dem_download_propagates_http_errors_without_writing_a_file(self):
        response = MagicMock()
        response.raise_for_status.side_effect = RuntimeError("HTTP failure")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "dem.tif"
            with patch("projects.terrain.requests.get", return_value=response):
                with self.assertRaisesRegex(RuntimeError, "HTTP failure"):
                    download_dem(self.project, output_path)
            self.assertFalse(output_path.exists())

    def test_slope_raster_contains_expected_gradient_in_degrees(self):
        import rasterio
        
        with tempfile.TemporaryDirectory() as temp_dir:
            dem_path = Path(temp_dir) / "dem.tif"
            slope_path = Path(temp_dir) / "slope.tif"
            profile = {
                "driver": "GTiff",
                "height": 3,
                "width": 3,
                "count": 1,
                "dtype": "float32",
                "crs": "EPSG:4326",
                "transform": from_origin(0, 3, 1, 1),
            }
            with rasterio.open(dem_path, "w", **profile) as dataset:
                dataset.write(
                    np.array(
                        [[0, 1, 2], [0, 1, 2], [0, 1, 2]],
                        dtype=np.float32,
                    ),
                    1,
                )

            generate_slope_raster(dem_path, slope_path)

            with rasterio.open(slope_path) as dataset:
                slope = dataset.read(1)
                self.assertEqual(dataset.dtypes[0], "float32")
                self.assertTrue(np.allclose(slope, 45.0))

    def test_terrain_population_samples_elevation_and_slope_at_cell_centroid(self):
        import numpy as np
        from projects.terrain import populate_terrain_data

        dem = MagicMock()
        dem.sample.return_value = iter([np.array([123.5])])
        slope = MagicMock()
        slope.sample.return_value = iter([np.array([12.25])])
        dem_context = MagicMock()
        dem_context.__enter__.return_value = dem
        slope_context = MagicMock()
        slope_context.__enter__.return_value = slope
        cell = MagicMock()
        cell.geometry.centroid.x = 1.5
        cell.geometry.centroid.y = 2.5
        project = MagicMock()
        project.grid_cells.all.return_value = [cell]

        with patch("rasterio.open") as mock_open:
            mock_open.side_effect = [dem_context, slope_context]

            populate_terrain_data(project, "dem.tif", "slope.tif")

        self.assertEqual(cell.elevation, 123.5)
        self.assertEqual(cell.slope, 12.25)
        cell.save.assert_called_once_with(update_fields=["elevation", "slope"])
        dem.sample.assert_called_once_with([(1.5, 2.5)])
        slope.sample.assert_called_once_with([(1.5, 2.5)])

    def test_road_import_skips_non_way_and_incomplete_elements(self):
        from projects.terrain import save_osm_roads

        with patch("projects.terrain.OSMRoad.objects.bulk_create") as bulk_create:
            save_osm_roads(
                {
                    "elements": [
                        {
                            "type": "way",
                            "id": 101,
                            "geometry": [
                                {"lon": 1, "lat": 2},
                                {"lon": 3, "lat": 4},
                            ],
                        },
                        {"type": "way", "id": 102, "geometry": [{"lon": 1, "lat": 2}]},
                        {"type": "node", "id": 103, "geometry": []},
                    ]
                }
            )

        roads = bulk_create.call_args.args[0]
        self.assertEqual(len(roads), 1)
        self.assertEqual(roads[0].osm_id, 101)
        self.assertEqual(roads[0].geometry.coords, ((1.0, 2.0), (3.0, 4.0)))
        bulk_create.assert_called_once_with(roads, ignore_conflicts=True)

    def test_osm_download_retries_a_timeout_before_returning_data(self):
        import requests
        from projects.terrain import download_osm_roads

        successful_response = MagicMock()
        successful_response.status_code = 200
        successful_response.json.return_value = {"elements": []}
        with (
            patch(
                "projects.terrain.requests.post",
                side_effect=[requests.exceptions.Timeout(), successful_response],
            ) as post,
            patch("projects.terrain.time.sleep"),
        ):
            result = download_osm_roads(self.project)

        self.assertEqual(result, {"elements": []})
        self.assertEqual(post.call_count, 2)


class NotificationAndAlertTests(ProjectAPITestCase):
    def test_user_can_read_own_notification_preferences(self):
        response = self.client.get(reverse("user_settings"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "receive_emails": True,
                "receive_invite_emails": True,
                "critical_incidents_only": False,
            },
        )

    def test_user_can_update_and_persist_notification_preferences(self):
        invite_alert_response = self.client.patch(
            reverse("user_settings"),
            {"receive_invite_emails": False},
            format="json",
        )

        self.assertEqual(invite_alert_response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.receive_emails)
        self.assertFalse(self.owner.receive_invite_emails)
        self.assertFalse(self.owner.critical_incidents_only)

        critical_alert_response = self.client.patch(
            reverse("user_settings"),
            {"critical_incidents_only": True},
            format="json",
        )

        self.assertEqual(critical_alert_response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.receive_emails)
        self.assertFalse(self.owner.receive_invite_emails)
        self.assertTrue(self.owner.critical_incidents_only)

        disable_email_response = self.client.patch(
            reverse("user_settings"),
            {"receive_emails": False},
            format="json",
        )

        self.assertEqual(disable_email_response.status_code, status.HTTP_200_OK)
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.receive_emails)
        self.assertFalse(self.owner.critical_incidents_only)
        self.assertFalse(self.owner.receive_invite_emails)

    def test_user_cannot_read_another_users_overview(self):
        other_user = User.objects.create_user(
            email="alerts-other@example.com",
            password="Testpass123!",
        )

        response = self.client.get(
            reverse("user_overview", args=[other_user.id])
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_overview_counts_new_incidents_as_alerts(self):
        Incident.objects.create(
            project=self.project,
            threat_class=self.threat_class,
            coordinates=Point(1, 1, srid=4326),
            confidence=90,
            grid_cell=self.cell,
            status=Incident.Status.NEW,
        )
        Device.objects.create(
            name="Overview sensor",
            location=Point(1, 1, srid=4326),
            project=self.project,
            grid_cell=self.cell,
            battery=90,
            status=Device.Status.ONLINE,
        )

        response = self.client.get(reverse("project_overview"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project_data = next(item for item in response.data if item["id"] == self.project.id)
        self.assertEqual(project_data["new_alerts"], 1)
        self.assertEqual(project_data["total_incidents"], 1)
        self.assertEqual(project_data["device_count"], 1)
        self.assertEqual(project_data["online_devices"], 1)

    def test_device_report_creates_incident_and_sends_notification(self):
        device = Device.objects.create(
            name="Notification sensor",
            location=Point(1, 1, srid=4326),
            project=self.project,
            grid_cell=self.cell,
            battery=80,
            status=Device.Status.ONLINE,
        )
        timestamp = timezone.now()

        with (
            patch.dict(os.environ, {"REAL_EMAIL": self.owner.email}),
            patch("projects.models.render_to_string", return_value="<p>Incident</p>"),
            patch("projects.models.resend.Batch.send") as send_email,
        ):
            response = self.client.post(
                reverse("report_incident", args=[device.id]),
                {
                    "threat_class": self.threat_class.id,
                    "timestamp": timestamp.isoformat(),
                    "confidence": 95,
                    "battery": 42,
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        device.refresh_from_db()
        self.assertEqual(device.battery, 42)
        self.assertEqual(device.last_seen, timestamp)
        incident = Incident.objects.get(device=device)
        self.assertEqual(incident.project, self.project)
        self.assertEqual(incident.threat_class, self.threat_class)
        self.assertEqual(incident.confidence, 95)
        self.assertEqual(incident.status, Incident.Status.NEW)
        send_email.assert_called_once()
        sent_params = send_email.call_args.args[0]
        self.assertEqual(len(sent_params), 1)
        self.assertEqual(sent_params[0]["to"], [self.owner.email])

    def test_device_report_respects_email_alert_preference(self):
        self.owner.receive_emails = False
        self.owner.save(update_fields=["receive_emails"])
        device = Device.objects.create(
            name="Muted notification sensor",
            location=Point(1, 1, srid=4326),
            project=self.project,
            grid_cell=self.cell,
            battery=80,
            status=Device.Status.ONLINE,
        )

        with (
            patch.dict(os.environ, {"REAL_EMAIL": self.owner.email}),
            patch("projects.models.resend.Batch.send") as send_email,
        ):
            response = self.client.post(
                reverse("report_incident", args=[device.id]),
                {
                    "threat_class": self.threat_class.id,
                    "timestamp": timezone.now().isoformat(),
                    "confidence": 95,
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        send_email.assert_not_called()

    def test_critical_incidents_only_emails_only_confidence_above_85(self):
        self.owner.critical_incidents_only = True
        self.owner.save(update_fields=["critical_incidents_only"])
        device = Device.objects.create(
            name="Critical-only notification sensor",
            location=Point(1, 1, srid=4326),
            project=self.project,
            grid_cell=self.cell,
            battery=80,
            status=Device.Status.ONLINE,
        )

        with (
            patch.dict(os.environ, {"REAL_EMAIL": self.owner.email}),
            patch("projects.models.render_to_string", return_value="<p>Incident</p>"),
            patch("projects.models.resend.Batch.send") as send_email,
        ):
            for confidence in (85, 86):
                response = self.client.post(
                    reverse("report_incident", args=[device.id]),
                    {
                        "threat_class": self.threat_class.id,
                        "timestamp": timezone.now().isoformat(),
                        "confidence": confidence,
                    },
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        send_email.assert_called_once()
        sent_params = send_email.call_args.args[0]
        self.assertEqual(len(sent_params), 1)
        self.assertEqual(sent_params[0]["to"], [self.owner.email])
