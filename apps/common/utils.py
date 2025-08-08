from django.conf import settings
from django.core.cache import cache


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def get_setting_cached(key: str, default: str | None = None) -> str | None:
    """Fetch a SystemSetting with small in-memory cache.

    Falls back to provided default when not found.
    """
    cache_key = f"system_setting:{key}"
    value = cache.get(cache_key)
    if value is not None:
        return value

    try:
        from apps.common.models import SystemSetting  # local import to avoid cycles
        obj = SystemSetting.objects.filter(key=key).only('value').first()
        value = obj.value if obj else default
    except Exception:
        value = default

    cache.set(cache_key, value, getattr(settings, 'SYSTEM_SETTINGS_CACHE_TTL', 600))
    return value
