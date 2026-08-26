from django.shortcuts import render
from rest_framework.views import APIView
from users.serializers import LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.serializers import UserSerializer
from users.models import User
from projects.models import Project, Incident, ThreatClass
from projects.serializers import ProjectSerializer, IncidentSerializer, ThreatClassSerializer

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

class IncidentViewSet(ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get("project")

        if project_id:
            project = Project.objects.get(pk=project_id)
            return Incident.objects.filter(project=project)
        else:
            return self.queryset