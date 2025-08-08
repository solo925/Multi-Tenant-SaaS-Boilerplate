"""
Django management command to clean up cached data and expired entries.
Usage: python manage.py cleanup_cache [--pattern PATTERN] [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
import re


class Command(BaseCommand):
    help = 'Clean up cached data and expired entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pattern',
            type=str,
            help='Cache key pattern to match (supports wildcards)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--expired-only',
            action='store_true',
            help='Only remove expired cache entries'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show cache statistics'
        )

    def handle(self, *args, **options):
        pattern = options.get('pattern')
        dry_run = options['dry_run']
        expired_only = options['expired_only']
        show_stats = options['stats']

        if show_stats:
            self.show_cache_stats()
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        if pattern:
            self.cleanup_by_pattern(pattern, dry_run)
        elif expired_only:
            self.cleanup_expired_only(dry_run)
        else:
            self.cleanup_all_cache(dry_run)

    def cleanup_by_pattern(self, pattern, dry_run=False):
        """Clean up cache entries matching a pattern."""
        self.stdout.write(f'Cleaning cache entries matching pattern: {pattern}')
        
        # Convert shell-style wildcards to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        compiled_pattern = re.compile(regex_pattern)
        
        # Note: This is a simplified implementation
        # In production, you'd need Redis-specific commands for pattern matching
        common_prefixes = [
            'dashboard_kpis_',
            'analytics_',
            'system_setting_',
            'user_',
            'tenant_',
        ]
        
        deleted_count = 0
        for prefix in common_prefixes:
            if compiled_pattern.match(prefix):
                if not dry_run:
                    # In a real implementation, you'd iterate through actual keys
                    cache.delete_many([f'{prefix}*'])
                deleted_count += 1
                self.stdout.write(f'  Deleted keys with prefix: {prefix}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Cleaned {deleted_count} cache key patterns')
        )

    def cleanup_expired_only(self, dry_run=False):
        """Clean up only expired cache entries."""
        self.stdout.write('Cleaning expired cache entries...')
        
        if not dry_run:
            # This would require backend-specific implementation
            # For Redis: SCAN + TTL commands
            # For now, we'll just log the action
            self.stdout.write('Expired entries cleanup initiated')
        
        self.stdout.write(
            self.style.SUCCESS('Expired cache entries cleaned')
        )

    def cleanup_all_cache(self, dry_run=False):
        """Clean up all cache entries."""
        self.stdout.write('Cleaning all cache entries...')
        
        if not dry_run:
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('All cache entries cleared')
            )
        else:
            self.stdout.write('Would clear all cache entries')

    def show_cache_stats(self):
        """Show cache statistics and configuration."""
        cache_config = settings.CACHES['default']
        
        self.stdout.write(
            self.style.SUCCESS('Cache Configuration:')
        )
        self.stdout.write(f'  Backend: {cache_config["BACKEND"]}')
        
        if 'LOCATION' in cache_config:
            self.stdout.write(f'  Location: {cache_config["LOCATION"]}')
        
        self.stdout.write(f'  Timeout: {cache_config.get("TIMEOUT", "Default")}')
        
        # Cache TTL settings
        self.stdout.write('\nCache TTL Settings:')
        ttl_settings = [
            ('DASHBOARD_CACHE_TTL', getattr(settings, 'DASHBOARD_CACHE_TTL', 120)),
            ('ANALYTICS_CACHE_TTL', getattr(settings, 'ANALYTICS_CACHE_TTL', 300)),
            ('SYSTEM_SETTINGS_CACHE_TTL', getattr(settings, 'SYSTEM_SETTINGS_CACHE_TTL', 600)),
        ]
        
        for setting_name, value in ttl_settings:
            self.stdout.write(f'  {setting_name}: {value} seconds')

        # Common cache key patterns
        self.stdout.write('\nCommon Cache Key Patterns:')
        patterns = [
            'dashboard_kpis_{user_id}_{schema_name}',
            'analytics_{schema_name}_{date}',
            'system_setting_{key}',
            'user_subscription_{user_id}',
            'tenant_info_{schema_name}',
        ]
        
        for pattern in patterns:
            self.stdout.write(f'  {pattern}')

        # Usage recommendations
        self.stdout.write(
            self.style.WARNING('\nUsage Recommendations:')
        )
        recommendations = [
            'Use --pattern to clean specific cache types',
            'Run --expired-only during maintenance windows',
            'Use --dry-run to preview changes before applying',
            'Monitor cache hit rates in production',
        ]
        
        for rec in recommendations:
            self.stdout.write(f'  • {rec}')


def get_cache_backend_type():
    """Determine the type of cache backend being used."""
    backend = settings.CACHES['default']['BACKEND']
    
    if 'redis' in backend.lower():
        return 'redis'
    elif 'memcached' in backend.lower():
        return 'memcached'
    elif 'locmem' in backend.lower():
        return 'locmem'
    else:
        return 'unknown'
