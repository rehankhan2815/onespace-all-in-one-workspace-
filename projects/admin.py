from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Project, ProjectMember

admin.site.register(Project)
admin.site.register(ProjectMember)