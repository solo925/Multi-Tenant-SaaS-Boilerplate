# Performance & Optimization Report

This document summarizes optimizations added to the Multi‑Tenant SaaS boilerplate.

## Implemented Optimizations

- Database indexes and constraints (apps/billing/models.py)
  - Subscription indexes: (user), (active, end_date), (end_date)
  - Payment indexes: (date), (user, date)
  - Unique active subscription per user (partial constraint)

- Query efficiency
  - Dashboard feed uses select_related + only to reduce columns/joins

- Caching (config/settings.py, apps/dashboard/views.py)
  - Global cache configured (LocMem by default)
  - Optional Redis cache via `REDIS_URL` for dev
  - Cached values with TTLs:
    - Dashboard KPIs: users_count, active_subscriptions_count, monthly_revenue
    - Analytics KPIs and daily series: revenue/signups
  - TTL envs (seconds):
    - DASHBOARD_CACHE_TTL (default 120)
    - ANALYTICS_CACHE_TTL (default 300)
    - SYSTEM_SETTINGS_CACHE_TTL (default 600)

- System settings helper (apps/common/utils.py)
  - get_setting_cached(key, default) for fast reads of SystemSetting

- Static assets
  - STATICFILES_DIRS includes /assets when present (CDN-friendly builds)

## Development Notes

- Clear cache using `make cache-clear`
- Emails are printed to console when `DEBUG=True`

## Operational Notes

- Cache invalidation
  - Delete affected keys on writes if immediate freshness is required

- Multitenancy
  - Prefix cache keys with schema name if values differ per tenant

- Testing
  - Add tests to assert cache paths (e.g., ensure cached responses avoid extra queries)
