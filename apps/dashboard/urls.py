from django.urls import path
from .views import dashboard_view, analytics_view, export_report_view, create_project_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('analytics/', analytics_view, name='analytics'),
    path('export-report/', export_report_view, name='export_report'),
    path('projects/create/', create_project_view, name='create_project'),
]
