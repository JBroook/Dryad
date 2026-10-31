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
    views.UserPatrolViewSet, 
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
router.register(
    r'projects/(?P<project_id>\d+)/patrols', 
    views.ProjectPatrolViewSet, 
    basename='project_patrols'
)

urlpatterns = [
    path('login/', views.LoginView.as_view(), name="login"),
    path('register/', views.RegisterView.as_view(), name="register"),
    path("forgot_password/", views.ForgotPasswordView.as_view()),
    path("reset_password/", views.ResetPasswordView.as_view()),
    path('verify_email/', views.VerifyEmailView.as_view(), name="verify_email"),
    path('delete_account/', views.DeleteAccountView.as_view(), name="delete_account"),
    path('', include(router.urls)),
    path('projects/<int:project_id>/connection_code', views.ProjectGetCodeView.as_view(), name="project_code"),
    path(
        'projects/<int:project_id>/routine_patrols/',
        views.ProjectRoutinePatrolView.as_view(),
        name="project_routine_patrols",
    ),
    path(
        'projects/<int:project_id>/routine_patrols/<int:routine_patrol_id>/',
        views.RoutinePatrolDetailView.as_view(),
        name="project_routine_patrol_detail",
    ),
    path(
        'projects/<int:project_id>/routine_patrols/<int:routine_patrol_id>/export/',
        views.RoutinePatrolGPXExportView.as_view(),
        name="routine_patrol_gpx_export",
    ),
    path(
        'projects/<int:project_id>/generate_routine_patrol_path/',
        views.GenerateRoutinePatrolPathView.as_view(),
        name="generate_routine_patrol_path",
    ),
    path(
        'users/<int:user_id>/routine_patrols/',
        views.UserRoutinePatrolListView.as_view(),
        name="user_routine_patrols",
    ),
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
    path('projects/<int:project_id>/incident_activity', views.IncidentActivityView.as_view(), name="incident_activity"),
    path('users/settings', views.UserSettingsView.as_view(), name="user_settings")
]