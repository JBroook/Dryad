import hashlib
import json
import math
import os
from datetime import timedelta
from xml.sax.saxutils import escape
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
import secrets
import string
import resend
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.views import APIView
from users.serializers import ForgotPasswordSerializer, LoginSerializer, RegisterSerializer, ResetPasswordSerializer, UserSettingsSerializer, VerifyEmailSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.viewsets import ModelViewSet
from users.serializers import UserSerializer
from users.models import User
from projects.models import ConnectionCode, Project, Incident, ThreatClass, Membership, Patrol, GridCell, Device, RoutinePatrol
from projects.permissions import require_project_role
from projects.serializers import (DeviceConnectSerializer, ProjectOverviewSerializer, ProjectSerializer, IncidentSerializer, 
ThreatClassSerializer, MembershipSerializer, PatrolSerializer,
GridCellSerializer, DeviceSerializer, RoutinePatrolSerializer)
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework.filters import OrderingFilter
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from django.db.models import Count
from django.db import IntegrityError, connection, transaction
from django.contrib.gis.geos import LineString, Point
from django.db.models.functions import TruncDate
from django.contrib.auth.hashers import check_password


class CRUDMessageMixin:
    def _message(self, action):
        serializer_class = getattr(self, "serializer_class", None)
        model = serializer_class.Meta.model
        resource = model._meta.verbose_name.title()
        return f"{resource} {action} successfully."

    def _with_message(self, response, action):
        if isinstance(response.data, list):
            response.data = {
                "results": response.data,
                "message": self._message(action),
            }
        else:
            response.data = {**response.data, "message": self._message(action)}
        return response

    def create(self, request, *args, **kwargs):
        return self._with_message(super().create(request, *args, **kwargs), "created")

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        action = "updated"
        return self._with_message(response, action)

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": self._message("deleted")},
            status=status.HTTP_200_OK,
        )


import logging
logger = logging.getLogger(__name__)


class LoginView(APIView):
    def post(self, request):
        logger.info("LOGIN DEBUG: Request received")

        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            logger.info("LOGIN DEBUG: Serializer validated")

            user = serializer.validated_data["user"]
            logger.info("LOGIN DEBUG: User retrieved")

            user_serializer = UserSerializer(user)
            logger.info("LOGIN DEBUG: User serialized")

            refresh = RefreshToken.for_user(user)
            logger.info("LOGIN DEBUG: JWT tokens generated")

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_serializer.data,
                "message": "Signed in successfully.",
            })

        except Exception:
            logger.exception("LOGIN DEBUG: Login failed")
            raise

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_active = False
        user.save()

        return Response(
            {"message": "Account deleted successfully."},
            status=status.HTTP_200_OK,
        )

class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "message": (
                    "If an account with that email exists, "
                    "a password reset link has been sent."
                )
            })

        token = secrets.token_urlsafe(32)

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        user.password_reset_token_hash = token_hash
        user.password_reset_token_expires_at = (
            timezone.now() + timedelta(minutes=15)
        )

        user.save(
            update_fields=[
                "password_reset_token_hash",
                "password_reset_token_expires_at",
            ]
        )

        user.send_password_reset_email(token)

        return Response({
            "message": (
                "If an account with that email exists, a password reset link has been sent."
            )
        })

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "user": UserSerializer(user).data,
                "message": "Account created successfully. Verify your email to continue.",
            },
            status=status.HTTP_201_CREATED,
        )

class VerifyEmailView(APIView):
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.verified:
            return Response(
                {"detail": "Email is already verified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.verification_code_hash:
            return Response(
                {"detail": "No verification code exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not check_password(code, user.verification_code_hash):
            return Response(
                {"detail": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.verified = True
        user.verification_code_hash = None

        user.save(
            update_fields=[
                "verified",
                "verification_code_hash"
            ]
        )

        return Response(
            {
                "detail": "Email verified successfully.",
                "message": "Email verified successfully.",
            },
            status=status.HTTP_200_OK,
        )
    
class UserViewSet(CRUDMessageMixin, ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ("retrieve", "update", "partial_update", "destroy"):
            return queryset.filter(pk=self.request.user.pk)
        email = self.request.query_params.get('email')

        if email:
            queryset = queryset.filter(email=email)

        return queryset
        

class ProjectViewSet(CRUDMessageMixin, ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(
            Q(members__user=self.request.user, members__accepted=True)
            | Q(owner=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        require_project_role(
            self.request,
            self.get_object().pk,
            Membership.Role.ADMIN,
        )
        if serializer.validated_data.get("status") is False:
            require_project_role(
                self.request,
                self.get_object().pk,
                Membership.Role.OWNER,
            )
        serializer.save()

    def perform_destroy(self, instance):
        require_project_role(
            self.request,
            instance.pk,
            Membership.Role.OWNER,
        )
        instance.delete()


class ProjectOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = Project.objects.annotate(
            member_count=Count('members', distinct=True),
            device_count=Count('devices', distinct=True),
            new_alerts=Count(
                'incidents',
                filter=Q(incidents__status=Incident.Status.NEW),
                distinct=True,
            ),
            total_incidents=Count('incidents', distinct=True),
            online_devices=Count(
                'devices',
                filter=Q(devices__status='online'),
                distinct=True,
            ),
        )

        project_id = request.query_params.get("project_id")

        if project_id:
            require_project_role(request, project_id)
            projects = projects.get(pk=project_id)
            many = False
        else:
            projects = projects.filter(
                Q(members__user=request.user, members__accepted=True)
                | Q(owner=request.user)
            ).distinct()
            many = True

        return Response(
            ProjectOverviewSerializer(projects, many=many).data,
            status=status.HTTP_200_OK
        )


class ThreatClassViewSet(ModelViewSet):
    queryset = ThreatClass.objects.all()
    serializer_class = ThreatClassSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]

class NumberInFilter(
    django_filters.BaseInFilter,
    django_filters.NumberFilter,
):
    pass

class IncidentFilter(django_filters.FilterSet):
    minimum_confidence = django_filters.NumberFilter(
        field_name="confidence",
        lookup_expr="gte",
    )

    status = django_filters.MultipleChoiceFilter(choices=Incident.Status.choices)
    threat_classes = NumberInFilter(
        field_name="threat_class_id",
        lookup_expr="in",
    )

    class Meta:
        model = Incident
        fields = [
            "minimum_confidence",
            "status",
            "threat_classes"
        ]

class IncidentViewSet(CRUDMessageMixin, ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = IncidentFilter

    ordering_fields = [
        "confidence",
        "timestamp"
    ]
    ordering = [
        "-timestamp"
    ]

    def get_queryset(self):
        queryset = Incident.objects.filter(
            Q(project__members__user=self.request.user, project__members__accepted=True)
            | Q(project__owner=self.request.user)
        ).distinct()
        project_id = self.request.query_params.get("project")

        if project_id:
            queryset = queryset.filter(project_id=project_id)

            search_param = self.request.query_params.get("search")
            if search_param:
                queryset = queryset.filter(threat_class__name__icontains=search_param)


        user_id = self.request.query_params.get("user_id")
        if user_id and str(self.request.user.pk) == user_id:
            queryset = queryset.filter(
                Q(project__members__user_id=user_id, project__members__accepted=True)
                | Q(project__owner_id=user_id)
            )
            
            search_param = self.request.query_params.get("search")
            if search_param:
                queryset = queryset.filter(threat_class__name__icontains=search_param)
            
        elif user_id:
            return Incident.objects.none()
        return queryset

    def perform_create(self, serializer):
        project = serializer.validated_data.get("project")
        if project is None:
            raise PermissionDenied("An incident project is required.")
        require_project_role(self.request, project.pk, Membership.Role.MANAGER)
        serializer.save()

    def perform_update(self, serializer):
        require_project_role(
            self.request,
            self.get_object().project_id,
            Membership.Role.MANAGER,
        )
        serializer.save()

    def perform_destroy(self, instance):
        require_project_role(
            self.request,
            instance.project_id,
            Membership.Role.MANAGER,
        )
        instance.delete()

class MembershipViewSet(CRUDMessageMixin, ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        require_project_role(self.request, self.kwargs["project_id"])
        queryset = self.queryset
        
        project_id = self.kwargs["project_id"]

        queryset = queryset.filter(
            project_id=project_id
        )

        search_param = self.request.query_params.get("search")
        if search_param:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_param) 
                |Q(user__last_name__icontains=search_param)
                |Q(user__email__icontains=search_param)
            )
            
        return queryset

    def perform_create(self, serializer):
        require_project_role(
            self.request,
            self.kwargs["project_id"],
            Membership.Role.ADMIN,
        )
        if serializer.validated_data.get("role") == Membership.Role.OWNER:
            require_project_role(
                self.request,
                self.kwargs["project_id"],
                Membership.Role.OWNER,
            )
        serializer.save()

    def perform_update(self, serializer):
        membership = self.get_object()
        caller = require_project_role(
            self.request,
            membership.project_id,
            Membership.Role.ADMIN,
        )
        if (
            membership.user_id == self.request.user.pk
            and serializer.validated_data.get("role", membership.role) != membership.role
        ):
            raise PermissionDenied("You cannot change your own project role.")
        if membership.role == Membership.Role.OWNER and (
            caller is None or caller.role != Membership.Role.OWNER
        ):
            raise PermissionDenied("Only the project owner can modify an owner.")
        if serializer.validated_data.get("role") == Membership.Role.OWNER and (
            caller is None or caller.role != Membership.Role.OWNER
        ):
            raise PermissionDenied("Only the project owner can assign the owner role.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user_id == self.request.user.pk:
            if instance.role == Membership.Role.OWNER:
                raise PermissionDenied("The project owner cannot leave their own project.")
            instance.delete()
            return

        caller = require_project_role(
            self.request,
            instance.project_id,
            Membership.Role.ADMIN,
        )
        if instance.role == Membership.Role.OWNER and (
            caller is None or caller.role != Membership.Role.OWNER
        ):
            raise PermissionDenied("Only the project owner can remove an owner.")
        instance.delete()

class UserMembershipsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if request.user.pk != user_id:
            raise PermissionDenied("You can only view your own memberships.")
        user = get_object_or_404(User, pk=user_id)
        return Response(
            MembershipSerializer(user.memberships, many=True).data,
            status=status.HTTP_200_OK
        )

class AcceptInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, membership_id):
        membership = get_object_or_404(
            Membership,
            pk=membership_id,
            user=request.user,
            accepted=False,
        )
        accepted_invite = request.data.get("accepted")
        if accepted_invite:
            membership.accepted = True
            membership.join_date = timezone.now()
            membership.save()
        else:
            membership.delete()

        return Response(
            {
                "message": (
                    "Project invitation accepted successfully."
                    if accepted_invite
                    else "Project invitation declined successfully."
                )
            },
            status=status.HTTP_200_OK
        )

class InviteMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        require_project_role(request, project_id, Membership.Role.MANAGER)
        email = request.query_params.get("email")

        if not email:
             return Response(
                {"details" : "Email address is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = get_object_or_404(User, email=email)
        project = get_object_or_404(Project, pk=project_id)

        try:
            membership = Membership.objects.create(
                project=project,
                user=user,
                role="viewer",
                invited_by=request.user,
            )
        except IntegrityError:
            return Response(
                {"details": "This user is already a member of this project"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.receive_invite_emails:
            resend.api_key = os.getenv("RESEND_API_KEY")
            sender_name = (
                f"{request.user.first_name} {request.user.last_name}".strip()
                or request.user.email
            )
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
            html = render_to_string(
                "emails/project_invitation.html",
                {
                    "project_name": project.name,
                    "sender_name": sender_name,
                    "invite_date": timezone.localtime(membership.invited_on).strftime(
                        "%B %d, %Y"
                    ),
                    "website_url": f"{frontend_url}/home/projects",
                },
            )
            params: resend.Emails.SendParams = {
                "from": "Dryad <onboarding@resend.dev>",
                "to": [os.getenv("REAL_EMAIL")],
                # "to": [user.email],  # Send directly to the invited member outside testing.
                "subject": f"{project.name}: Project Invitation",
                "html": html,
            }
            resend.Emails.send(params)

        return Response(
            {
                **MembershipSerializer(membership).data,
                "message": "Project invitation sent successfully.",
            },
            status=status.HTTP_201_CREATED
        )
    

class UserPatrolViewSet(CRUDMessageMixin, ModelViewSet):
    queryset = Patrol.objects.all()
    serializer_class = PatrolSerializer
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if str(request.user.pk) != str(kwargs["user_id"]):
            raise PermissionDenied("You can only access your own patrols.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
            many=True,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):
        return self.queryset.filter(
            members__user=self.request.user,
            members__accepted=True,
        ).distinct()

    def perform_update(self, serializer):
        require_project_role(
            self.request,
            self.get_object().project_id,
            Membership.Role.MANAGER,
        )
        serializer.save()

    def perform_destroy(self, instance):
        require_project_role(
            self.request,
            instance.project_id,
            Membership.Role.MANAGER,
        )
        instance.delete()

    def create(self, request, *args, **kwargs):
        patrols = request.data if isinstance(request.data, list) else [request.data]
        for patrol_data in patrols:
            project_data = patrol_data.get("project")
            project_id = (
                project_data.get("id")
                if isinstance(project_data, dict)
                else project_data
            )
            if project_id is None:
                raise PermissionDenied("A project is required to create a patrol.")
            require_project_role(request, project_id, Membership.Role.MANAGER)
        return super().create(request, *args, **kwargs)


class UserRoutinePatrolListView(ListAPIView):
    serializer_class = RoutinePatrolSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.pk != int(self.kwargs["user_id"]):
            return RoutinePatrol.objects.none()

        return RoutinePatrol.objects.filter(
            project__members__user=self.request.user,
            project__members__accepted=True,
        ).select_related(
            "project",
            "created_by__user",
        ).distinct().order_by("-created_at")


class GridCellViewSet(CRUDMessageMixin, ModelViewSet):
    queryset = GridCell.objects.all()
    serializer_class = GridCellSerializer
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in SAFE_METHODS:
            require_project_role(
                request,
                kwargs["project_id"],
                Membership.Role.MANAGER,
            )

    def get_queryset(self):
        require_project_role(self.request, self.kwargs["project_id"])
        queryset = self.queryset

        project_id = self.kwargs["project_id"]

        return queryset.filter(
            project_id=project_id
        )

class DeviceViewSet(CRUDMessageMixin, ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in SAFE_METHODS:
            require_project_role(
                request,
                kwargs["project_id"],
                Membership.Role.MANAGER,
            )

    def get_queryset(self):
        require_project_role(self.request, self.kwargs["project_id"])
        queryset = self.queryset

        project_id = self.kwargs["project_id"]

        return queryset.filter(
            project_id=project_id
        )

class ProjectPatrolViewSet(CRUDMessageMixin, ModelViewSet):
    queryset = Patrol.objects.all()
    serializer_class = PatrolSerializer
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in SAFE_METHODS:
            require_project_role(
                request,
                kwargs["project_id"],
                Membership.Role.MANAGER,
            )

    def get_queryset(self):
        require_project_role(self.request, self.kwargs["project_id"])
        queryset = self.queryset

        project_id = self.kwargs["project_id"]

        return queryset.filter(
            project_id=project_id
        )


class ProjectRoutinePatrolView(CRUDMessageMixin, ListCreateAPIView):
    serializer_class = RoutinePatrolSerializer
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in SAFE_METHODS:
            require_project_role(
                request,
                kwargs["project_id"],
                Membership.Role.MANAGER,
            )

    def get_queryset(self):
        require_project_role(self.request, self.kwargs["project_id"])
        return RoutinePatrol.objects.filter(
            project_id=self.kwargs["project_id"]
        ).select_related("project", "created_by__user").order_by("-created_at")

    def perform_create(self, serializer):
        project = get_object_or_404(
            Project,
            pk=self.kwargs["project_id"],
            members__user=self.request.user,
            members__accepted=True,
        )
        creator = get_object_or_404(
            Membership,
            project=project,
            user=self.request.user,
        )
        serializer.save(project=project, created_by=creator)


class RoutinePatrolDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_patrol(self, request, project_id, routine_patrol_id):
        require_project_role(request, project_id)
        return get_object_or_404(
            RoutinePatrol.objects.select_related("project", "created_by__user"),
            pk=routine_patrol_id,
            project_id=project_id,
        )

    def get(self, request, project_id, routine_patrol_id):
        patrol = self.get_patrol(request, project_id, routine_patrol_id)
        return Response(
            RoutinePatrolSerializer(patrol).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, project_id, routine_patrol_id):
        require_project_role(request, project_id, Membership.Role.MANAGER)
        patrol = self.get_patrol(request, project_id, routine_patrol_id)
        patrol.delete()
        return Response(
            {"message": "Routine Patrol deleted successfully."},
            status=status.HTTP_200_OK,
        )


class RoutinePatrolGPXExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id, routine_patrol_id):
        patrol = get_object_or_404(
            RoutinePatrol.objects.select_related("project").filter(
                Q(project__members__user=request.user, project__members__accepted=True)
                | Q(project__owner=request.user)
            ).distinct(),
            pk=routine_patrol_id,
            project_id=project_id,
        )
        waypoints = "\n".join(
            f'      <trkpt lat="{latitude:.7f}" lon="{longitude:.7f}"></trkpt>'
            for longitude, latitude in patrol.path.coords
        )
        gpx = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<gpx version="1.1" creator="Dryad" '
            'xmlns="http://www.topografix.com/GPX/1/1">\n'
            "  <metadata>\n"
            f"    <name>{escape(patrol.name)}</name>\n"
            "  </metadata>\n"
            "  <trk>\n"
            f"    <name>{escape(patrol.name)}</name>\n"
            "    <trkseg>\n"
            f"{waypoints}\n"
            "    </trkseg>\n"
            "  </trk>\n"
            "</gpx>\n"
        )
        response = HttpResponse(gpx, content_type="application/gpx+xml; charset=utf-8")
        response["Content-Disposition"] = (
            f'attachment; filename="routine-patrol-{patrol.pk}.gpx"'
        )
        return response


class GenerateRoutinePatrolPathView(APIView):
    permission_classes = [IsAuthenticated]
    hotspot_risk_threshold = 0.8

    def post(self, request, project_id):
        require_project_role(request, project_id, Membership.Role.MANAGER)
        project = get_object_or_404(Project, pk=project_id)

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    risk_score,
                    ST_X(hotspot_center),
                    ST_Y(hotspot_center)
                FROM (
                    SELECT
                        MAX(risk_score) AS risk_score,
                        ST_Centroid(ST_Collect(geometry)) AS hotspot_center
                    FROM (
                        SELECT
                            risk_score,
                            geometry,
                            ST_ClusterDBSCAN(geometry, 0, 1)
                                OVER () AS hotspot_cluster
                        FROM {GridCell._meta.db_table}
                        WHERE project_id = %s
                          AND risk_score >= %s
                    ) AS high_risk_cells
                    GROUP BY hotspot_cluster
                ) AS risk_hotspots
                ORDER BY risk_score DESC
                """,
                [project.id, self.hotspot_risk_threshold],
            )
            hotspot_rows = cursor.fetchall()

        hotspots = [
            (
                risk_score,
                Point(longitude, latitude, srid=4326),
            )
            for risk_score, longitude, latitude in hotspot_rows
        ]
        if len(hotspots) < 2:
            return Response(
                {
                    "detail": (
                        "At least two separate very-high-risk hotspots (risk score 0.8 or "
                        "higher) are needed to generate a patrol path."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        remaining = hotspots
        remaining.sort(key=lambda hotspot: hotspot[0], reverse=True)
        ordered_points = [remaining.pop(0)[1]]

        while remaining:
            current_point = ordered_points[-1]
            nearest_index = min(
                range(len(remaining)),
                key=lambda index: self._distance_meters(
                    current_point,
                    remaining[index][1],
                ),
            )
            ordered_points.append(remaining.pop(nearest_index)[1])

        route = LineString(
            [point.coords for point in ordered_points],
            srid=4326,
        )
        return Response(
            {
                "path": json.loads(route.geojson),
                "hotspot_count": len(ordered_points),
                "message": "Patrol path generated successfully.",
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _distance_meters(first, second):
        first_latitude, first_longitude = map(math.radians, (first.y, first.x))
        second_latitude, second_longitude = map(math.radians, (second.y, second.x))
        latitude_delta = second_latitude - first_latitude
        longitude_delta = second_longitude - first_longitude
        haversine = (
            math.sin(latitude_delta / 2) ** 2
            + math.cos(first_latitude)
            * math.cos(second_latitude)
            * math.sin(longitude_delta / 2) ** 2
        )
        return 6_371_000 * 2 * math.asin(math.sqrt(haversine))


class ProjectGetCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        require_project_role(request, project_id, Membership.Role.MANAGER)
        characters = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(characters) for _ in range(6))

        ConnectionCode.objects.create(
            code = code,
            project=Project.objects.get(pk=project_id)
        )

        return Response(
            {
                "code": code,
                "message": "Device connection code created successfully.",
            },
            status=status.HTTP_201_CREATED
        )

class DeviceConnectionView(APIView):
    def post(self, request):
        serializer = DeviceConnectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]
        coordinate = serializer.validated_data["coordinate"]
        battery = serializer.validated_data["battery"]

        try:
            connection_code = ConnectionCode.objects.get(code=code)
        except ConnectionCode.DoesNotExist:
            return Response({
                "detail" : "Invalid Connection Code"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not connection_code.is_valid:
            return Response(
                {"detail": "Connection code has expired or was already used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        grid_cell = connection_code.project.grid_cells.filter(
            geometry__covers=coordinate
        ).first()

        if grid_cell is None:
            return Response(
                {"detail": "No grid cell matches this device location."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        device = Device.objects.create(
            name=f"Device-{code}",
            location=coordinate,
            project=connection_code.project,
            battery=battery,
            grid_cell=grid_cell,
            status="online"
        )

        connection_code.used_at = timezone.now()
        connection_code.device = device
        connection_code.save(update_fields=["used_at","device"])

        project_threat_classes = list(
            connection_code.project.threat_classes.values_list(
                "threat_class_id",
                flat=True,
            )
        )

        return Response(
            {
                "message": "Device connected successfully.",
                "device_id": device.id,
                "threat_classes": project_threat_classes,
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        code = request.query_params.get("code")

        try:
            connection_code = ConnectionCode.objects.get(code=code)
        except ConnectionCode.DoesNotExist:
            return Response(
                {"status": "not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if connection_code.expires_at < timezone.now():
            return Response(
                {"status": "expired"},
                status=status.HTTP_200_OK,
            )

        if connection_code.used_at:
            return Response(
                {
                    "status": "claimed",
                    "device": DeviceSerializer(connection_code.device).data
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"status": "available"},
            status=status.HTTP_200_OK,
        )

class DeviceReportView(APIView):
    def post(self, request, device_id):
        device = get_object_or_404(Device, id=device_id)
        threat_class_id = request.data.get("threat_class")
        threat_class = get_object_or_404(ThreatClass, id=threat_class_id)
        timestamp = parse_datetime(request.data.get("timestamp"))
        confidence = request.data.get("confidence")
        device.report_incident(
            threat_class=threat_class,
            timestamp=timestamp,
            confidence=confidence
        )

        return Response(
            {
                "details": "Report received successfully.",
                "message": "Incident report received successfully.",
            },
            status=status.HTTP_201_CREATED,
        )

class PatrolCompletionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, patrol_id):
        try:
            patrol = Patrol.objects.get(pk=patrol_id)
        except Patrol.DoesNotExist:
            return Response({"details" : "Patrol does not exist"}, status=status.HTTP_404_NOT_FOUND)

        patrol_status = request.data.get("patrol_status")
        incident_status = request.data.get("incident_status")
        longitude = request.data.get("longitude")
        latitude = request.data.get("latitude")

        if patrol_status not in Patrol.Status.values:
            return Response(
                {"details": "A valid patrol status is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        membership = require_project_role(
            request,
            patrol.project_id,
            Membership.Role.VIEWER,
        )
        if membership is not None and membership.role == Membership.Role.VIEWER:
            if not patrol.members.filter(pk=membership.pk).exists():
                raise PermissionDenied("Viewers can only update patrols assigned to them.")
            if patrol.status != Patrol.Status.PENDING:
                raise PermissionDenied("Viewers can only update pending assigned patrols.")
            if patrol_status not in (
                Patrol.Status.CANCELLED,
                Patrol.Status.COMPLETED,
            ):
                raise PermissionDenied("Viewers can only cancel or complete assigned patrols.")
            if patrol_status == Patrol.Status.CANCELLED and incident_status is not None:
                raise PermissionDenied("Cancelling a patrol cannot change its incident.")

        if patrol_status == Patrol.Status.CANCELLED:
            patrol.delete()
            return Response(
                {
                    "details": "Success!",
                    "message": "Patrol cancelled successfully.",
                },
                status=status.HTTP_200_OK,
            )

        if incident_status not in (
            Incident.Status.CONFIRMED,
            Incident.Status.DISMISSED,
        ):
            return Response(
                {"details": "A confirmed or dismissed incident status is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        patrol.status = patrol_status
        patrol.save(update_fields=["status"])
        patrol.incident.status = incident_status
        if (
            incident_status == Incident.Status.CONFIRMED
            and latitude is not None
            and longitude is not None
        ):
            patrol.incident.coordinates = Point(longitude, latitude, srid=4326)
        patrol.incident.save()

        return Response(
            {
                "details": "Success!",
                "message": "Patrol completed and incident status updated successfully.",
            },
            status=status.HTTP_200_OK,
        )

class PatrolAssignView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, incident_id):
        try:
            incident = Incident.objects.get(pk=incident_id)
        except Incident.DoesNotExist:
            return Response({"details" : "Incident does not exist"}, status=status.HTTP_404_NOT_FOUND)

        require_project_role(
            request,
            incident.project_id,
            Membership.Role.MANAGER,
        )
        assignee_ids = request.data.get("assignee_ids")
        if assignee_ids is None and request.data.get("assignee_id") is not None:
            assignee_ids = [request.data.get("assignee_id")]

        if not isinstance(assignee_ids, list) or not assignee_ids:
            return Response(
                {"details" : "Assignees must be provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            assignee_ids = list(dict.fromkeys(int(assignee_id) for assignee_id in assignee_ids))
        except (TypeError, ValueError):
            return Response(
                {"details" : "Assignee IDs must be valid"},
                status=status.HTTP_400_BAD_REQUEST
            )

        assignees = list(Membership.objects.filter(
            pk__in=assignee_ids,
            project=incident.project,
            accepted=True,
        ))
        if len(assignees) != len(assignee_ids):
            return Response(
                {"details" : "One or more assignees do not belong to this project"},
                status=status.HTTP_404_NOT_FOUND
            )

        assigner = get_object_or_404(
            Membership,
            project=incident.project,
            user=request.user,
            accepted=True,
        )

        incident.status = Incident.Status.REVIEWING
        incident.save()

        patrol = Patrol.objects.filter(
            incident=incident,
            status=Patrol.Status.PENDING
        ).order_by("assigned_at").first()
        if patrol is None:
            patrol = Patrol.objects.create(
                project=incident.project,
                incident=incident,
                target=incident.coordinates,
                assigned_by=assigner
            )

        patrol.members.add(*assignees)

        return Response(
            {
                **PatrolSerializer(patrol).data,
                "message": "Patrol assigned successfully.",
            },
            status=status.HTTP_200_OK
        )

class CalculateProjectRiskView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        from projects.BNN import calculate_project_risk

        require_project_role(request, project_id, Membership.Role.ADMIN)
        project = get_object_or_404(
            Project,
            id=project_id
        )

        calculate_project_risk(project)

        project.train_count += 1
        project.last_trained = timezone.now()
        project.save()

        return Response({
            "message": "Risk calculation completed.",
            "project": project.id,
        }, status=status.HTTP_200_OK)

class UserOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if request.user.pk != user_id:
            raise PermissionDenied("You can only view your own overview.")
        user = get_object_or_404(
            User,
            id=user_id
        )

        user_projects = Project.objects.filter(members__user=user, members__accepted=True)
        active_projects = user_projects.filter(status=True).count()

        new_incidents = 0
        online_devices = 0
        total_incidents = 0
        for project in user_projects:
            new_incidents += project.incidents.filter(status=Incident.Status.NEW).count()
            online_devices += project.devices.filter(status=Device.Status.ONLINE).count()
            total_incidents += project.incidents.count()

        return Response({
            "active_projects" : active_projects,
            "new_incidents" : new_incidents,
            "online_devices" : online_devices,
            "total_incidents" : total_incidents
        }, status=status.HTTP_200_OK)

class UserSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user

        settings_serializer = UserSettingsSerializer(user)

        return Response(
            settings_serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request):
        settings_serializer = UserSettingsSerializer(
            self.request.user,
            data=self.request.data,
            partial=True
        )

        settings_serializer.is_valid(raise_exception=True)
        settings_serializer.save()

        return Response(
            {"message": "Settings saved successfully."},
            status=status.HTTP_200_OK
        )

class IncidentActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        require_project_role(request, project_id)
        project = get_object_or_404(Project, pk=project_id)

        today = timezone.localdate()
        seven_days_ago = today - timedelta(days=6)

        queryset = (
            project.incidents
            .filter(
                timestamp__date__gte=seven_days_ago,
                timestamp__date__lte=today,
            )
            .annotate(day=TruncDate("timestamp"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        counts = {
            row["day"]: row["count"]
            for row in queryset
        }

        result = [
            {
                "day": seven_days_ago + timedelta(days=i),
                "count": counts.get(seven_days_ago + timedelta(days=i), 0),
            }
            for i in range(7)
        ]

        return Response(result)

class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        try:
            user = User.objects.get(
                password_reset_token_hash=token_hash
            )
        except User.DoesNotExist:
            return Response(
                {
                    "error": "Invalid or expired reset token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            not user.password_reset_token_expires_at
            or user.password_reset_token_expires_at < timezone.now()
        ):
            return Response(
                {
                    "error": "Invalid or expired reset token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)

        user.password_reset_token_hash = None
        user.password_reset_token_expires_at = None

        user.save(
            update_fields=[
                "password",
                "password_reset_token_hash",
                "password_reset_token_expires_at",
            ]
        )

        return Response({
            "message": "Password has been reset successfully."
        })