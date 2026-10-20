from django.contrib.gis.geos import LineString, Point, Polygon
from django.test import TestCase
from django.urls import reverse
from xml.etree import ElementTree
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import GridCell, Incident, Membership, Patrol, Project, RoutinePatrol, ThreatClass
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
        for member in self.assignees:
            self.assertEqual(
                Patrol.objects.get(members=member).status,
                Patrol.Status.COMPLETED,
            )

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
            "Routine patrol created successfully.",
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

    def test_manager_cannot_invite_or_change_project_settings(self):
        manager_user = User.objects.create_user(
            email="manager@example.com",
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
        invite_response = self.client.post(
            reverse("invite", args=[self.project.id]),
            {"email": "new-member@example.com"},
        )

        self.assertEqual(settings_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(role_response.status_code, status.HTTP_200_OK)
        self.assertEqual(invite_response.status_code, status.HTTP_403_FORBIDDEN)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Patrol Test Project")

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
