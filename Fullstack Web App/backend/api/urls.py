from django.urls import path, include
from . import views
from .  import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'users', views.UserViewSet, basename='user')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'threat_classes', views.ThreatClassViewSet, basename='threat_class')
router.register(r'incidents', views.IncidentViewSet, basename='incident')
router.register(r'members', views.MembershipViewSet, basename='member')
router.register(r'patrols', views.PatrolViewSet, basename='patrol')

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="login"),
    path('', include(router.urls))
]