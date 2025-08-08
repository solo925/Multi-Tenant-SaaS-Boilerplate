from django.urls import path
from .views import dashboard_view, analytics_view

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('analytics/', analytics_view, name='analytics'),
]
