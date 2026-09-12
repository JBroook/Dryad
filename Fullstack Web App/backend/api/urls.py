from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'users', views.UserViewSet, basename='user')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'threat_classes', views.ThreatClassViewSet, basename='threat_class')
router.register(r'incidents', views.IncidentViewSet, basename='incident')
router.register(r'members', views.MembershipViewSet, basename='member')
router.register(r'patrols', views.PatrolViewSet, basename='patrol')
router.register(
    r'projects/(?P<project_id>\d+)/grid_cells', 
    views.GridCellViewSet, 
    basename='project_grid_cells'
)
router.register(
    r'projects/(?P<project_id>\d+)/devices', 
    views.DeviceViewSet, 
    basename='project_devices'
)

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="login"),
    path('', include(router.urls)),
    path('projects/<int:project_id>/connection_code', views.ProjectGetCodeView.as_view(), name="project_code"),
    path('devices/connect', views.DeviceConnectionView.as_view(), name="connect_device")
]