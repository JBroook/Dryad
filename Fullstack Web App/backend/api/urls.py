from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'users', views.UserViewSet, basename='user')
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'threat_classes', views.ThreatClassViewSet, basename='threat_class')
router.register(r'incidents', views.IncidentViewSet, basename='incident')
router.register(
    r'users/(?P<user_id>\d+)/patrols', 
    views.PatrolViewSet, 
    basename='user_patrol'
)
router.register(
    r'projects/(?P<project_id>\d+)/members', 
    views.MembershipViewSet, 
    basename='member'
)
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
    path('devices/connect', views.DeviceConnectionView.as_view(), name="connect_device"),
    path('devices/<int:device_id>/report', views.DeviceReportView.as_view(), name="report_incident"),
    path('projects/<int:project_id>/invite', views.InviteMemberView.as_view(), name="invite"),
    path('patrols/<int:patrol_id>/complete_patrol', views.PatrolCompletionView.as_view(), name="complete_patrol"),
    path('incidents/<int:incident_id>/assign_patrol', views.PatrolAssignView.as_view(), name="assign_patrol"),
    path('projects/<int:project_id>/calculate_risk', views.CalculateProjectRiskView.as_view(), name="calculate_risk"),
    path('users/<int:user_id>/overview', views.UserOverviewView.as_view(), name="user_overview"),
    path('users/<int:user_id>/memberships', views.UserMembershipsView.as_view(), name="user_memberships"),
    path('projects/overview', views.ProjectOverviewView.as_view(), name="project_overview"),
    path('memberships/<int:membership_id>/accept_invite', views.AcceptInviteView.as_view(), name="accept_invite"),
]