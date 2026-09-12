from django.contrib import admin
from . import models

admin.site.register(models.Project)
admin.site.register(models.ThreatClass)
admin.site.register(models.ProjectThreatClass)
admin.site.register(models.Membership)
admin.site.register(models.Incident)
admin.site.register(models.Device)
admin.site.register(models.Patrol)
admin.site.register(models.GridCell)
admin.site.register(models.ConnectionCode)