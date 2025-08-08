"""
Django management command to perform comprehensive health checks.
Usage: python manage.py health_check [--component COMPONENT] [--verbose]
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection, connections
from django.conf import settings
from django.contrib.auth import get_user_model
from apps.tenants.models import Client
from apps.billing.models import Subscription, Payment
import time
import os
import sys


class Command(BaseCommand):
    help = 'Perform comprehensive health checks on the application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--component',
            type=str,
            choices=['database', 'cache', 'tenants', 'billing', 'all'],
            default='all',
            help='Specific component to check'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Timeout for checks in seconds (default: 30)'
        )

    def handle(self, *args, **options):
        component = options['component']
        verbose = options['verbose']
        timeout = options['timeout']
        
        self.verbose = verbose
        self.timeout = timeout
        
        self.stdout.write(
            self.style.SUCCESS('🏥 Multi-Tenant SaaS Health Check')
        )
        self.stdout.write('=' * 50)
        
        results = {}
        
        if component in ['database', 'all']:
            results['database'] = self.check_database()
            
        if component in ['cache', 'all']:
            results['cache'] = self.check_cache()
            
        if component in ['tenants', 'all']:
            results['tenants'] = self.check_tenants()
            
        if component in ['billing', 'all']:
            results['billing'] = self.check_billing()
            
        # Additional checks for 'all'
        if component == 'all':
            results['environment'] = self.check_environment()
            results['security'] = self.check_security()
        
        # Summary
        self.print_summary(results)
        
        # Exit with error code if any checks failed
        if any(not result['healthy'] for result in results.values()):
            sys.exit(1)

    def check_database(self):
        """Check database connectivity and basic operations."""
        self.stdout.write('\n📊 Database Health Check')
        self.stdout.write('-' * 30)
        
        result = {'healthy': True, 'issues': []}
        
        try:
            # Test basic connectivity
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                response_time = (time.time() - start_time) * 1000
            
            if response_time > 1000:  # 1 second
                result['issues'].append(f'Slow database response: {response_time:.2f}ms')
                
            self.stdout.write(f'✅ Database connectivity: OK ({response_time:.2f}ms)')
            
            # Check schema count
            User = get_user_model()
            user_count = User.objects.count()
            tenant_count = Client.objects.count()
            
            self.stdout.write(f'✅ Users: {user_count}')
            self.stdout.write(f'✅ Tenants: {tenant_count}')
            
            # Test tenant schema access
            if tenant_count > 0:
                sample_tenant = Client.objects.first()
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                        [sample_tenant.schema_name]
                    )
                    if cursor.fetchone():
                        self.stdout.write(f'✅ Tenant schema access: OK')
                    else:
                        result['issues'].append(f'Tenant schema {sample_tenant.schema_name} not found')
                        result['healthy'] = False
            
        except Exception as e:
            result['healthy'] = False
            result['issues'].append(f'Database error: {str(e)}')
            self.stdout.write(self.style.ERROR(f'❌ Database: {str(e)}'))
        
        return result

    def check_cache(self):
        """Check cache connectivity and operations."""
        self.stdout.write('\n🚀 Cache Health Check')
        self.stdout.write('-' * 25)
        
        result = {'healthy': True, 'issues': []}
        
        try:
            # Test basic cache operations
            test_key = 'health_check_test'
            test_value = 'test_value_123'
            
            start_time = time.time()
            cache.set(test_key, test_value, 60)
            cached_value = cache.get(test_key)
            response_time = (time.time() - start_time) * 1000
            
            if cached_value != test_value:
                result['healthy'] = False
                result['issues'].append('Cache set/get operation failed')
            else:
                self.stdout.write(f'✅ Cache operations: OK ({response_time:.2f}ms)')
            
            # Clean up test key
            cache.delete(test_key)
            
            # Check cache backend
            cache_backend = settings.CACHES['default']['BACKEND']
            self.stdout.write(f'✅ Cache backend: {cache_backend.split(".")[-1]}')
            
        except Exception as e:
            result['healthy'] = False
            result['issues'].append(f'Cache error: {str(e)}')
            self.stdout.write(self.style.ERROR(f'❌ Cache: {str(e)}'))
        
        return result

    def check_tenants(self):
        """Check tenant-specific functionality."""
        self.stdout.write('\n🏢 Tenant Health Check')
        self.stdout.write('-' * 27)
        
        result = {'healthy': True, 'issues': []}
        
        try:
            total_tenants = Client.objects.count()
            active_tenants = Client.objects.filter(is_active=True).count()
            trial_tenants = Client.objects.filter(on_trial=True).count()
            
            self.stdout.write(f'✅ Total tenants: {total_tenants}')
            self.stdout.write(f'✅ Active tenants: {active_tenants}')
            self.stdout.write(f'✅ Trial tenants: {trial_tenants}')
            
            # Check for tenants without domains
            tenants_without_domains = Client.objects.filter(domains__isnull=True).count()
            if tenants_without_domains > 0:
                result['issues'].append(f'{tenants_without_domains} tenants without domains')
            
            # Check for expired trials
            from datetime import date
            expired_trials = Client.objects.filter(
                on_trial=True,
                paid_until__lt=date.today()
            ).count()
            
            if expired_trials > 0:
                result['issues'].append(f'{expired_trials} expired trial tenants')
                
        except Exception as e:
            result['healthy'] = False
            result['issues'].append(f'Tenant check error: {str(e)}')
            self.stdout.write(self.style.ERROR(f'❌ Tenants: {str(e)}'))
        
        return result

    def check_billing(self):
        """Check billing and subscription functionality."""
        self.stdout.write('\n💳 Billing Health Check')
        self.stdout.write('-' * 26)
        
        result = {'healthy': True, 'issues': []}
        
        try:
            total_subscriptions = Subscription.objects.count()
            active_subscriptions = Subscription.objects.filter(active=True).count()
            total_payments = Payment.objects.count()
            
            self.stdout.write(f'✅ Total subscriptions: {total_subscriptions}')
            self.stdout.write(f'✅ Active subscriptions: {active_subscriptions}')
            self.stdout.write(f'✅ Total payments: {total_payments}')
            
            # Check for users with multiple active subscriptions
            from django.db.models import Count
            users_with_multiple_subs = Subscription.objects.filter(active=True)\
                .values('user').annotate(count=Count('id')).filter(count__gt=1).count()
            
            if users_with_multiple_subs > 0:
                result['issues'].append(f'{users_with_multiple_subs} users with multiple active subscriptions')
            
            # Check for subscriptions without plans
            subs_without_plans = Subscription.objects.filter(plan__isnull=True).count()
            if subs_without_plans > 0:
                result['issues'].append(f'{subs_without_plans} subscriptions without plans')
                
        except Exception as e:
            result['healthy'] = False
            result['issues'].append(f'Billing check error: {str(e)}')
            self.stdout.write(self.style.ERROR(f'❌ Billing: {str(e)}'))
        
        return result

    def check_environment(self):
        """Check environment configuration."""
        self.stdout.write('\n🌍 Environment Health Check')
        self.stdout.write('-' * 30)
        
        result = {'healthy': True, 'issues': []}
        
        # Check critical settings
        critical_settings = [
            ('SECRET_KEY', 'Secret key configuration'),
            ('DEBUG', 'Debug mode setting'),
            ('ALLOWED_HOSTS', 'Allowed hosts configuration'),
        ]
        
        for setting_name, description in critical_settings:
            if hasattr(settings, setting_name):
                value = getattr(settings, setting_name)
                if setting_name == 'SECRET_KEY' and value == 'dev-secret-key':
                    result['issues'].append('Using default secret key')
                elif setting_name == 'DEBUG' and value and not self.is_development():
                    result['issues'].append('DEBUG=True in production')
                else:
                    self.stdout.write(f'✅ {description}: OK')
            else:
                result['issues'].append(f'Missing {setting_name} setting')
        
        # Check disk space
        disk_usage = self.check_disk_space()
        if disk_usage > 90:
            result['issues'].append(f'High disk usage: {disk_usage}%')
        else:
            self.stdout.write(f'✅ Disk usage: {disk_usage}%')
        
        return result

    def check_security(self):
        """Check security configuration."""
        self.stdout.write('\n🔒 Security Health Check')
        self.stdout.write('-' * 27)
        
        result = {'healthy': True, 'issues': []}
        
        # Check HTTPS settings in production
        if not self.is_development():
            security_settings = [
                ('SECURE_SSL_REDIRECT', True),
                ('SESSION_COOKIE_SECURE', True),
                ('CSRF_COOKIE_SECURE', True),
            ]
            
            for setting_name, expected_value in security_settings:
                if getattr(settings, setting_name, None) != expected_value:
                    result['issues'].append(f'{setting_name} should be {expected_value} in production')
        
        # Check for default admin user
        User = get_user_model()
        if User.objects.filter(email='admin@example.com').exists():
            result['issues'].append('Default admin user exists')
        
        if not result['issues']:
            self.stdout.write('✅ Security configuration: OK')
        
        return result

    def check_disk_space(self):
        """Check available disk space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            return (used / total) * 100
        except:
            return 0

    def is_development(self):
        """Check if running in development environment."""
        return getattr(settings, 'DEBUG', False) or 'localhost' in getattr(settings, 'ALLOWED_HOSTS', [])

    def print_summary(self, results):
        """Print health check summary."""
        self.stdout.write('\n📋 Health Check Summary')
        self.stdout.write('=' * 30)
        
        total_checks = len(results)
        healthy_checks = sum(1 for r in results.values() if r['healthy'])
        
        self.stdout.write(f'Total checks: {total_checks}')
        self.stdout.write(f'Healthy: {healthy_checks}')
        self.stdout.write(f'Issues: {total_checks - healthy_checks}')
        
        # List all issues
        all_issues = []
        for component, result in results.items():
            for issue in result['issues']:
                all_issues.append(f'{component}: {issue}')
        
        if all_issues:
            self.stdout.write('\n⚠️  Issues Found:')
            for issue in all_issues:
                self.stdout.write(self.style.WARNING(f'  • {issue}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n🎉 All checks passed!'))
        
        self.stdout.write('')
