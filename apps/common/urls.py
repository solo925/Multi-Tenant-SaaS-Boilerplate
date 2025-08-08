from django.urls import path
from .views import (
    system_settings_view,
    system_settings_create_view,
    system_settings_delete_view,
)

app_name = 'common'

urlpatterns = [
    path('system-settings/', system_settings_view, name='system_settings'),
    path('system-settings/create/', system_settings_create_view, name='system_settings_create'),
    path('system-settings/<int:pk>/delete/', system_settings_delete_view, name='system_settings_delete'),
]


