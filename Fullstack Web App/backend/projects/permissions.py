from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from .models import Membership, Project


ROLE_LEVELS = {
    Membership.Role.VIEWER: 0,
    Membership.Role.MANAGER: 1,
    Membership.Role.ADMIN: 2,
    Membership.Role.OWNER: 3,
}


def require_project_role(request, project_id, minimum_role=Membership.Role.VIEWER):
    project = get_object_or_404(Project, pk=project_id)
    membership = Membership.objects.filter(
        project=project,
        user=request.user,
        accepted=True,
    ).first()

    if project.owner_id == request.user.pk:
        return membership

    if membership is None:
        raise PermissionDenied("You are not an accepted member of this project.")

    if ROLE_LEVELS[membership.role] < ROLE_LEVELS[minimum_role]:
        raise PermissionDenied("Your project role does not allow this action.")

    return membership


def require_membership_role(membership, minimum_role):
    if ROLE_LEVELS[membership.role] < ROLE_LEVELS[minimum_role]:
        raise PermissionDenied("Your project role does not allow this action.")
