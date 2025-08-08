"""
API serializers for common app models and utilities.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SystemSetting


User = get_user_model()


class SystemSettingSerializer(serializers.ModelSerializer):
    """Serializer for system settings with validation."""
    
    class Meta:
        model = SystemSetting
        fields = ['id', 'key', 'value', 'description']
        read_only_fields = ['id']
    
    def validate_key(self, value):
        """Validate system setting key format."""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError(
                "Key must contain only alphanumeric characters, hyphens, and underscores"
            )
        
        if len(value) > 100:
            raise serializers.ValidationError("Key must be 100 characters or less")
        
        return value.lower()
    
    def validate_value(self, value):
        """Validate system setting value."""
        if len(value) > 10000:  # Reasonable limit for text fields
            raise serializers.ValidationError("Value is too long (max 10,000 characters)")
        
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information."""
    
    subscription_status = serializers.SerializerMethodField()
    tenant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'is_active', 'date_joined',
            'subscription_status', 'tenant_count'
        ]
        read_only_fields = ['id', 'email', 'date_joined']
    
    def get_subscription_status(self, obj):
        """Get user's current subscription status."""
        try:
            from apps.billing.models import Subscription
            from datetime import date
            
            active_sub = Subscription.objects.filter(
                user=obj, 
                active=True,
                end_date__gte=date.today()
            ).first()
            
            if active_sub:
                return {
                    'active': True,
                    'plan_name': active_sub.plan.name if active_sub.plan else 'Unknown',
                    'end_date': active_sub.end_date,
                }
            else:
                return {'active': False}
        except:
            return {'active': False}
    
    def get_tenant_count(self, obj):
        """Get number of tenants associated with user."""
        try:
            from apps.tenants.models import Client
            # This is a simplified count - in reality, you'd need to check
            # which tenants the user has access to
            return Client.objects.filter(is_active=True).count()
        except:
            return 0


class TenantInfoSerializer(serializers.Serializer):
    """Serializer for tenant information (not model-based)."""
    
    schema_name = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    on_trial = serializers.BooleanField(read_only=True)
    paid_until = serializers.DateField(read_only=True)
    created_on = serializers.DateField(read_only=True)
    domain_count = serializers.IntegerField(read_only=True)
    user_count = serializers.IntegerField(read_only=True)


class CacheStatsSerializer(serializers.Serializer):
    """Serializer for cache statistics and health information."""
    
    backend_type = serializers.CharField(read_only=True)
    total_keys = serializers.IntegerField(read_only=True)
    hit_rate = serializers.FloatField(read_only=True)
    miss_rate = serializers.FloatField(read_only=True)
    memory_usage = serializers.CharField(read_only=True)
    configuration = serializers.DictField(read_only=True)


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check results."""
    
    component = serializers.CharField(read_only=True)
    healthy = serializers.BooleanField(read_only=True)
    response_time_ms = serializers.FloatField(read_only=True)
    details = serializers.DictField(read_only=True)
    issues = serializers.ListField(
        child=serializers.CharField(),
        read_only=True
    )
    timestamp = serializers.DateTimeField(read_only=True)


class BulkOperationSerializer(serializers.Serializer):
    """Serializer for bulk operations on multiple objects."""
    
    operation = serializers.ChoiceField(
        choices=['create', 'update', 'delete', 'activate', 'deactivate']
    )
    object_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    data = serializers.DictField(required=False)
    
    def validate_object_ids(self, value):
        """Validate that object IDs are unique."""
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Object IDs must be unique")
        return value


class PaginationInfoSerializer(serializers.Serializer):
    """Serializer for pagination metadata."""
    
    count = serializers.IntegerField(read_only=True)
    next = serializers.URLField(read_only=True, allow_null=True)
    previous = serializers.URLField(read_only=True, allow_null=True)
    page_size = serializers.IntegerField(read_only=True)
    page_number = serializers.IntegerField(read_only=True)
    total_pages = serializers.IntegerField(read_only=True)


class ErrorDetailSerializer(serializers.Serializer):
    """Serializer for detailed error information."""
    
    error_code = serializers.CharField(read_only=True)
    error_message = serializers.CharField(read_only=True)
    field_errors = serializers.DictField(read_only=True, required=False)
    timestamp = serializers.DateTimeField(read_only=True)
    request_id = serializers.CharField(read_only=True, required=False)


class MetricsSerializer(serializers.Serializer):
    """Serializer for application metrics and KPIs."""
    
    metric_name = serializers.CharField(read_only=True)
    metric_value = serializers.FloatField(read_only=True)
    metric_unit = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    tags = serializers.DictField(read_only=True, required=False)
    
    class Meta:
        """Additional metadata for metrics."""
        description = "Key performance indicators and application metrics"


# Utility functions for serializers

def validate_email_domain(email):
    """Validate email domain against allowed domains."""
    from django.conf import settings
    
    allowed_domains = getattr(settings, 'ALLOWED_EMAIL_DOMAINS', None)
    if allowed_domains:
        domain = email.split('@')[1].lower()
        if domain not in allowed_domains:
            raise serializers.ValidationError(
                f"Email domain '{domain}' is not allowed"
            )
    return email


def sanitize_html_content(content):
    """Sanitize HTML content to prevent XSS attacks."""
    import re
    
    # Remove script tags
    content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove on* event handlers
    content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    
    # Remove javascript: URLs
    content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
    
    return content


def format_currency(amount, currency='USD'):
    """Format currency amount for display."""
    if currency == 'USD':
        return f"${amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def calculate_percentage(part, total):
    """Calculate percentage with safe division."""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)
