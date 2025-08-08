from django.urls import path
from .views import (
    create_tenant_view,
    list_tenants_view,
    tenant_detail_view,
    edit_tenant_view,
    add_domain_view,
    set_primary_domain_view,
    delete_domain_view,
    delete_tenant_view,
)

app_name = 'tenants'

urlpatterns = [
    path('', list_tenants_view, name='list'),
    path('create/', create_tenant_view, name='create'),
    path('<int:pk>/', tenant_detail_view, name='detail'),
    path('<int:pk>/edit/', edit_tenant_view, name='edit'),
    path('<int:pk>/domains/add/', add_domain_view, name='domain_add'),
    path('<int:pk>/domains/<int:domain_id>/primary/', set_primary_domain_view, name='domain_primary'),
    path('<int:pk>/domains/<int:domain_id>/delete/', delete_domain_view, name='domain_delete'),
    path('<int:pk>/delete/', delete_tenant_view, name='delete'),
]

