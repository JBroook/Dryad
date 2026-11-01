from datetime import timedelta
from io import BytesIO
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.gis.geos import Point, Polygon
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from PIL import Image

from projects.models import ConnectionCode, Device, GridCell, Membership, Project
from users.models import User


class ProfilePictureTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.client = APIClient()
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="Testpass123!",
            first_name="Profile",
            last_name="User",
        )
        self.client.force_authenticate(user=self.user)

    def test_profile_picture_is_null_by_default_and_can_be_uploaded_and_cleared(self):
        url = reverse("user-detail", args=[self.user.pk])
        initial_response = self.client.get(url)
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)
        self.assertIsNone(initial_response.data["profile_picture"])

        image_buffer = BytesIO()
        Image.new("RGB", (1, 1), color="red").save(image_buffer, format="PNG")
        image_buffer.seek(0)
        upload_response = self.client.patch(
            url,
            {
                "profile_picture": SimpleUploadedFile(
                    "profile.png",
                    image_buffer.read(),
                    content_type="image/png",
                )
            },
            format="multipart",
        )

        self.assertEqual(upload_response.status_code, status.HTTP_200_OK)
        self.assertIn("/media/profile_pictures/", upload_response.data["profile_picture"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_picture.name)
        self.assertTrue(self.user.profile_picture.storage.exists(self.user.profile_picture.name))

        clear_response = self.client.patch(
            url,
            {"profile_picture": None},
            format="json",
        )

        self.assertEqual(clear_response.status_code, status.HTTP_200_OK)
        self.assertIsNone(clear_response.data["profile_picture"])
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_picture)


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


class ProjectMembershipPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="test-password",
            first_name="Owner",
            last_name="User",
        )
        self.manager = User.objects.create_user(
            email="manager@example.com",
            password="test-password",
            first_name="Manager",
            last_name="User",
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="test-password",
            first_name="Admin",
            last_name="User",
        )
        self.invitee = User.objects.create_user(
            email="invitee@example.com",
            password="test-password",
            first_name="Invitee",
            last_name="User",
        )
        self.project = Project.objects.create(
            name="Membership Test Project",
            status=True,
            region="Test region",
            color="#0055ff",
            owner=self.owner,
            coordinates="0,0",
            surface_area=2500,
            monitoring_area=Polygon.from_bbox((0, 0, 10, 10)),
        )
        Membership.objects.create(
            project=self.project,
            user=self.manager,
            invited_by=self.owner,
            role=Membership.Role.MANAGER,
            accepted=True,
        )
        Membership.objects.create(
            project=self.project,
            user=self.admin,
            invited_by=self.owner,
            role=Membership.Role.ADMIN,
            accepted=True,
        )
        self.member = Membership.objects.create(
            project=self.project,
            user=self.invitee,
            invited_by=self.owner,
            role=Membership.Role.VIEWER,
            accepted=True,
        )
        self.client.force_authenticate(user=self.manager)

    def test_forest_map_warning_is_returned_only_on_first_visit(self):
        url = reverse(
            "project_forest_map_opened",
            args=[self.project.pk],
        )

        first_response = self.client.post(url)
        second_response = self.client.post(url)

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertTrue(first_response.data["show_warning"])
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertFalse(second_response.data["show_warning"])
        self.member.refresh_from_db()
        self.assertTrue(self.member.opened)

    def test_non_member_cannot_mark_forest_map_as_opened(self):
        outsider = User.objects.create_user(
            email="outsider@example.com",
            password="Testpass123!",
        )
        self.client.force_authenticate(user=outsider)

        response = self.client.post(
            reverse(
                "project_forest_map_opened",
                args=[self.project.pk],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.member.refresh_from_db()
        self.assertFalse(self.member.opened)

    def test_manager_can_invite_a_member_but_cannot_change_roles(self):
        new_invitee = User.objects.create_user(
            email="new-invitee@example.com",
            password="test-password",
            first_name="New",
            last_name="Invitee",
        )
        invite_response = self.client.post(
            f"{reverse('invite', args=[self.project.id])}?email={new_invitee.email}",
        )
        self.assertEqual(invite_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Membership.objects.get(project=self.project, user=new_invitee).role,
            Membership.Role.VIEWER,
        )

        role_response = self.client.patch(
            reverse("member-detail", args=[self.project.id, self.member.id]),
            {"role": Membership.Role.MANAGER},
            format="json",
        )
        self.assertEqual(role_response.status_code, status.HTTP_403_FORBIDDEN)
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, Membership.Role.VIEWER)

        remove_response = self.client.delete(
            reverse("member-detail", args=[self.project.id, self.member.id]),
        )
        self.assertEqual(remove_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Membership.objects.filter(pk=self.member.id).exists())

    def test_admin_can_change_member_roles(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("member-detail", args=[self.project.id, self.member.id]),
            {"role": Membership.Role.MANAGER},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member.refresh_from_db()
        self.assertEqual(self.member.role, Membership.Role.MANAGER)

    def test_admin_can_remove_members(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            reverse("member-detail", args=[self.project.id, self.member.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Membership.objects.filter(pk=self.member.id).exists())

    def test_viewer_can_leave_project(self):
        self.client.force_authenticate(user=self.invitee)

        response = self.client.delete(
            reverse("member-detail", args=[self.project.id, self.member.id]),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Membership.objects.filter(
                project=self.project,
                user=self.invitee,
            ).exists()
        )

    def test_manager_can_leave_project(self):
        manager_membership = Membership.objects.get(
            project=self.project,
            user=self.manager,
        )
        self.client.force_authenticate(user=self.manager)

        response = self.client.delete(
            reverse(
                "member-detail",
                args=[self.project.id, manager_membership.id],
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Membership.objects.filter(
                project=self.project,
                user=self.manager,
            ).exists()
        )

    def test_project_owner_cannot_leave_project(self):
        owner_membership = Membership.objects.create(
            project=self.project,
            user=self.owner,
            invited_by=self.owner,
            role=Membership.Role.OWNER,
            accepted=True,
        )
        self.client.force_authenticate(user=self.owner)

        response = self.client.delete(
            reverse(
                "member-detail",
                args=[self.project.id, owner_membership.id],
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            Membership.objects.filter(pk=owner_membership.id).exists()
        )

    def test_manager_cannot_request_project_risk_calculation(self):
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(
            reverse("calculate_risk", args=[self.project.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
