from django.db import models
from django.conf import settings


class Project(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='projects')
    tenant_schema_name = models.CharField(max_length=63, help_text='Schema name this project belongs to')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name
