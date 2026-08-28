from rest_framework import status
from rest_framework.views import APIView
from users.serializers import LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.serializers import UserSerializer
from users.models import User
from projects.models import Project, Incident, ThreatClass, Membership, Patrol
from projects.serializers import ProjectSerializer, IncidentSerializer, ThreatClassSerializer, MembershipSerializer, PatrolSerializer
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

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
    filter_backends = [DjangoFilterBackend]
    filterset_class = IncidentFilter

    def get_queryset(self):
        project_id = self.request.query_params.get("project")

        if project_id:
            queryset = Incident.objects.filter(project_id=project_id)

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
        project_id = self.request.query_params.get("project")

        if project_id:
            project = Project.objects.get(pk=project_id)
            queryset = Membership.objects.filter(project=project)

            search_param = self.request.query_params.get("search")
            if search_param:
                queryset = queryset.filter(
                    Q(user__first_name__icontains=search_param) 
                    |Q(user__last_name__icontains=search_param)
                    |Q(user__email__icontains=search_param)
                )
                
            return queryset

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