from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "tenant_schema_name", "created_at")
    search_fields = ("name", "description", "tenant_schema_name")

# Register your models here.
