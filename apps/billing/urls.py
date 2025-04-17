from django.urls import path
from .views import plans_view

urlpatterns = [
    path('plans/', plans_view, name='plans'),
    path('subscribe/<int:plan_id>/', subscribe_to_plan, name='subscribe'),
    path('checkout/<int:plan_id>/', mock_checkout, name='checkout'),


]
