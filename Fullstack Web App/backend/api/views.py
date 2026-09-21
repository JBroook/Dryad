from django.utils import timezone
import secrets
import string
from projects.BNN import calculate_project_risk
from rest_framework import status
from rest_framework.views import APIView
from users.serializers import LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.serializers import UserSerializer
from users.models import User
from projects.models import ConnectionCode, Project, Incident, ThreatClass, Membership, Patrol, GridCell, Device
from projects.serializers import (DeviceConnectSerializer, ProjectSerializer, IncidentSerializer, 
ThreatClassSerializer, MembershipSerializer, PatrolSerializer,
GridCellSerializer, DeviceSerializer)
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework.filters import OrderingFilter
from django.shortcuts import get_object_or_404

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        user_serializer = UserSerializer(user)

        refresh = RefreshToken.for_user(user)

        return Response({
            "access" : str(refresh.access_token),
            "refresh" : str(refresh),
            "user" : user_serializer.data
        })

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        email = self.request.query_params.get('email')

        if email:
            queryset = queryset.filter(email=email)

        return queryset
        

class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ThreatClassViewSet(ModelViewSet):
    queryset = ThreatClass.objects.all()
    serializer_class = ThreatClassSerializer

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

class IncidentViewSet(ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
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
        project_id = self.request.query_params.get("project")

        if project_id:
            queryset = super().get_queryset().filter(project_id=project_id)

            search_param = self.request.query_params.get("search")
            if search_param:
                queryset = queryset.filter(threat_class__name__icontains=search_param)

            return queryset
        else:
            return self.queryset

class MembershipViewSet(ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer

    def get_queryset(self):
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

class InviteMemberView(APIView):
    def post(self, request, project_id):
        email = request.query_params.get("email")

        if not email:
             return Response(
                {"details" : "Email address is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"details" : "User with this email does not exists"},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response(
                {"details" : "This project doesn't exist"},
                status=status.HTTP_404_NOT_FOUND
            )

        membership = Membership.objects.create(
            project=project,
            user=user,
            role="viewer"
        )
        
        return Response(
            MembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED
        )
    

class PatrolViewSet(ModelViewSet):
    queryset = Patrol.objects.all()
    serializer_class = PatrolSerializer

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
        queryset = self.queryset
        user_id = self.kwargs["user_id"]

        return queryset.filter(
            member__user_id=user_id
        )

class GridCellViewSet(ModelViewSet):
    queryset = GridCell.objects.all()
    serializer_class = GridCellSerializer
    
    def get_queryset(self):
        queryset = self.queryset

        project_id = self.kwargs["project_id"]

        return queryset.filter(
            project_id=project_id
        )

class DeviceViewSet(ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    def get_queryset(self):
        queryset = self.queryset

        project_id = self.kwargs["project_id"]

        return queryset.filter(
            project_id=project_id
        )

class ProjectGetCodeView(APIView):
    def post(self, request, project_id):
        characters = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(characters) for _ in range(6))

        ConnectionCode.objects.create(
            code = code,
            project=Project.objects.get(pk=project_id)
        )

        return Response(
            {"code" : code},
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

        device = Device.objects.create(
            name=f"Device-{code}",
            location = coordinate,
            project = connection_code.project,
            battery=battery,
            status="online"
        )

        connection_code.used_at = timezone.now()
        connection_code.device = device
        connection_code.save(update_fields=["used_at","device"])

        return Response(
            {
                "message": "Device connected successfully.",
                "device_id": device.id,
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

class PatrolCompletionView(APIView):
    def post(self, request, patrol_id):
        try:
            patrol = Patrol.objects.get(pk=patrol_id)
        except Patrol.DoesNotExist:
            return Response({"details" : "Patrol does not exist"}, status=status.HTTP_404_NOT_FOUND)

        patrol_status = request.data.get("patrol_status")
        incident_status = request.data.get("incident_status")

        if patrol_status:
            patrol.status = patrol_status
            patrol.save()

            if patrol_status!="cancelled":
                if not incident_status:
                    return Response(
                        {"details" : "Incident status not provided"}, 
                        status=status.HTTP_400_BAD_REQUEST
                        ) 
                
                patrol.incident.status = incident_status
                patrol.incident.save()

                return Response({
                    "details" : "Success!"
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "details" : "Success!"
                }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"details" : "Patrol status not provided"}, 
                status=status.HTTP_400_BAD_REQUEST
                )

class PatrolAssignView(APIView):
    def post(self, request, incident_id):
        try:
            incident = Incident.objects.get(pk=incident_id)
        except Incident.DoesNotExist:
            return Response({"details" : "Incident does not exist"}, status=status.HTTP_404_NOT_FOUND)

        assigner_id = request.data.get("assigner_id")
        assignee_id = request.data.get("assignee_id")

        if assigner_id and assignee_id:
            try:
                assignee = Membership.objects.get(pk=assignee_id)
                assigner = Membership.objects.get(pk=assigner_id)
            except Membership.DoesNotExist:
                return Response({"details" : "Members do not exist"}, status=status.HTTP_404_NOT_FOUND)

            patrol = Patrol.objects.create(
                project=incident.project,
                incident=incident,
                member=assignee,
                target=incident.coordinates,
                assigned_by=assigner
            )

            return Response(
                PatrolSerializer(patrol).data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"details" : "Members not provided"}, 
                status=status.HTTP_400_BAD_REQUEST
                )

class CalculateProjectRiskView(APIView):
    def post(self, request, project_id):
        project = get_object_or_404(
            Project,
            id=project_id
        )

        calculate_project_risk(project)

        return Response({
            "message": "Risk calculation completed.",
            "project": project.id,
        }, status=status.HTTP_200_OK)