"""
API views for common app functionality.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.core.cache import cache
from django.conf import settings
from django.db import connection
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import SystemSetting
from .serializers import (
    SystemSettingSerializer, UserProfileSerializer, TenantInfoSerializer,
    CacheStatsSerializer, HealthCheckSerializer, MetricsSerializer
)
import time
import json


User = get_user_model()


class SystemSettingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing system settings via API."""
    
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter queryset based on query parameters."""
        queryset = super().get_queryset()
        key_filter = self.request.query_params.get('key', None)
        
        if key_filter:
            queryset = queryset.filter(key__icontains=key_filter)
        
        return queryset.order_by('key')
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update multiple system settings."""
        settings_data = request.data.get('settings', [])
        
        if not isinstance(settings_data, list):
            return Response(
                {'error': 'Settings must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_count = 0
        errors = []
        
        for setting_data in settings_data:
            try:
                key = setting_data.get('key')
                value = setting_data.get('value')
                description = setting_data.get('description', '')
                
                if not key:
                    errors.append({'error': 'Key is required', 'data': setting_data})
                    continue
                
                setting, created = SystemSetting.objects.update_or_create(
                    key=key,
                    defaults={'value': value, 'description': description}
                )
                updated_count += 1
                
                # Invalidate cache for this setting
                cache.delete(f"system_setting_{key}")
                
            except Exception as e:
                errors.append({'error': str(e), 'data': setting_data})
        
        return Response({
            'updated_count': updated_count,
            'errors': errors
        })
    
    @action(detail=False, methods=['delete'])
    def clear_cache(self, request):
        """Clear system settings cache."""
        try:
            # Clear all system setting cache keys
            cache.delete_pattern("system_setting_*")
            return Response({'message': 'System settings cache cleared'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_api(request):
    """Get current user's profile information."""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def tenant_info_api(request):
    """Get current tenant information."""
    try:
        from apps.tenants.models import Client
        
        schema_name = connection.schema_name
        
        if schema_name == 'public':
            return Response({
                'schema_name': 'public',
                'name': 'Public Schema',
                'is_active': True,
                'message': 'Currently in public schema'
            })
        
        try:
            tenant = Client.objects.get(schema_name=schema_name)
            
            # Get additional stats
            domain_count = tenant.domains.count()
            user_count = User.objects.count()  # Users in current tenant schema
            
            data = {
                'schema_name': tenant.schema_name,
                'name': tenant.name,
                'is_active': tenant.is_active,
                'on_trial': tenant.on_trial,
                'paid_until': tenant.paid_until,
                'created_on': tenant.created_on,
                'domain_count': domain_count,
                'user_count': user_count,
            }
            
            serializer = TenantInfoSerializer(data)
            return Response(serializer.data)
            
        except Client.DoesNotExist:
            return Response(
                {'error': f'Tenant with schema {schema_name} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def cache_stats_api(request):
    """Get cache statistics and health information."""
    try:
        cache_config = settings.CACHES['default']
        backend_type = cache_config['BACKEND'].split('.')[-1]
        
        # Test cache operations
        start_time = time.time()
        test_key = 'api_cache_test'
        cache.set(test_key, 'test_value', 60)
        cache.get(test_key)
        cache.delete(test_key)
        response_time = (time.time() - start_time) * 1000
        
        data = {
            'backend_type': backend_type,
            'response_time_ms': round(response_time, 2),
            'configuration': {
                'backend': cache_config['BACKEND'],
                'location': cache_config.get('LOCATION', 'N/A'),
                'timeout': cache_config.get('TIMEOUT', 300),
            },
            'health': 'OK' if response_time < 100 else 'SLOW',
            'timestamp': timezone.now()
        }
        
        # Add Redis-specific stats if available
        if 'redis' in backend_type.lower():
            try:
                import redis
                from django_redis import get_redis_connection
                
                redis_conn = get_redis_connection("default")
                info = redis_conn.info()
                
                data['redis_info'] = {
                    'used_memory_human': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                }
                
                # Calculate hit rate
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                total = hits + misses
                
                data['hit_rate'] = round((hits / total * 100), 2) if total > 0 else 0
                data['miss_rate'] = round((misses / total * 100), 2) if total > 0 else 0
                
            except Exception as redis_error:
                data['redis_error'] = str(redis_error)
        
        serializer = CacheStatsSerializer(data)
        return Response(serializer.data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_check_api(request):
    """Comprehensive health check endpoint."""
    component = request.query_params.get('component', 'all')
    
    results = {}
    overall_health = True
    
    # Database health check
    if component in ['database', 'all']:
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            response_time = (time.time() - start_time) * 1000
            
            results['database'] = {
                'healthy': True,
                'response_time_ms': round(response_time, 2),
                'details': {'connection': 'OK'},
                'issues': []
            }
        except Exception as e:
            results['database'] = {
                'healthy': False,
                'response_time_ms': 0,
                'details': {'error': str(e)},
                'issues': [f'Database error: {str(e)}']
            }
            overall_health = False
    
    # Cache health check
    if component in ['cache', 'all']:
        try:
            start_time = time.time()
            test_key = 'health_check_cache_test'
            cache.set(test_key, 'test', 60)
            cache.get(test_key)
            cache.delete(test_key)
            response_time = (time.time() - start_time) * 1000
            
            results['cache'] = {
                'healthy': True,
                'response_time_ms': round(response_time, 2),
                'details': {'operations': 'OK'},
                'issues': []
            }
        except Exception as e:
            results['cache'] = {
                'healthy': False,
                'response_time_ms': 0,
                'details': {'error': str(e)},
                'issues': [f'Cache error: {str(e)}']
            }
            overall_health = False
    
    # Application health check
    if component in ['application', 'all']:
        try:
            user_count = User.objects.count()
            
            results['application'] = {
                'healthy': True,
                'response_time_ms': 0,
                'details': {
                    'user_count': user_count,
                    'schema': connection.schema_name,
                    'debug_mode': settings.DEBUG
                },
                'issues': []
            }
        except Exception as e:
            results['application'] = {
                'healthy': False,
                'response_time_ms': 0,
                'details': {'error': str(e)},
                'issues': [f'Application error: {str(e)}']
            }
            overall_health = False
    
    # Overall response
    response_data = {
        'overall_health': overall_health,
        'timestamp': timezone.now(),
        'checks': results
    }
    
    status_code = status.HTTP_200_OK if overall_health else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(response_data, status=status_code)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def metrics_api(request):
    """Get application metrics and KPIs."""
    try:
        from apps.billing.models import Subscription, Payment
        from apps.tenants.models import Client
        from django.db.models import Count, Sum
        from datetime import date, timedelta
        
        # Calculate metrics
        today = date.today()
        last_30_days = today - timedelta(days=30)
        
        metrics = [
            {
                'metric_name': 'total_users',
                'metric_value': User.objects.count(),
                'metric_unit': 'count',
                'timestamp': timezone.now(),
                'tags': {'category': 'users'}
            },
            {
                'metric_name': 'active_subscriptions',
                'metric_value': Subscription.objects.filter(active=True).count(),
                'metric_unit': 'count',
                'timestamp': timezone.now(),
                'tags': {'category': 'billing'}
            },
            {
                'metric_name': 'total_tenants',
                'metric_value': Client.objects.count(),
                'metric_unit': 'count',
                'timestamp': timezone.now(),
                'tags': {'category': 'tenants'}
            },
            {
                'metric_name': 'monthly_revenue',
                'metric_value': float(
                    Payment.objects.filter(
                        date__gte=last_30_days
                    ).aggregate(total=Sum('amount'))['total'] or 0
                ),
                'metric_unit': 'currency',
                'timestamp': timezone.now(),
                'tags': {'category': 'billing', 'period': '30_days'}
            }
        ]
        
        serializer = MetricsSerializer(metrics, many=True)
        return Response({
            'metrics': serializer.data,
            'generated_at': timezone.now()
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, permissions.IsAdminUser])
def clear_all_cache_api(request):
    """Clear all cache entries."""
    try:
        cache.clear()
        return Response({
            'message': 'All cache entries cleared',
            'timestamp': timezone.now()
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def status_api(request):
    """Simple status endpoint for load balancers."""
    return Response({
        'status': 'OK',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })


# Utility function for API responses
def create_error_response(message, status_code=status.HTTP_400_BAD_REQUEST, details=None):
    """Create a standardized error response."""
    response_data = {
        'error': message,
        'timestamp': timezone.now(),
    }
    
    if details:
        response_data['details'] = details
    
    return Response(response_data, status=status_code)


def create_success_response(data, message=None):
    """Create a standardized success response."""
    response_data = {
        'success': True,
        'data': data,
        'timestamp': timezone.now(),
    }
    
    if message:
        response_data['message'] = message
    
    return Response(response_data)
