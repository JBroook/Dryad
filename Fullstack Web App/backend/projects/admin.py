from django.contrib import admin
from .models import Project, ThreatClass, ProjectThreatClass, Membership

admin.site.register(Project)
admin.site.register(ThreatClass)
admin.site.register(ProjectThreatClass)
admin.site.register(Membership)