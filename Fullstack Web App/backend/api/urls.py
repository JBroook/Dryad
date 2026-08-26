from django.urls import path, include
from . import views
from .views import UserViewSet, ProjectViewSet, ThreatClassViewSet, IncidentViewSet, MembershipViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'threat_classes', ThreatClassViewSet, basename='threat_class')
router.register(r'incidents', IncidentViewSet, basename='incident')
router.register(r'members', MembershipViewSet, basename='member')

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="login"),
    path('', include(router.urls))
]