from decimal import Decimal
from django.db import connection
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from apps.users.models import User
from apps.billing.models import Subscription, Payment
from .models import Project
from .forms import ProjectForm
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from django.conf import settings
import csv

@login_required
def dashboard_view(request):
    # Check if user has an active subscription
    sub = Subscription.objects.filter(user=request.user, active=True).first()  # type: ignore
    
    # If no subscription or subscription has expired
    if not sub or sub.end_date < now().date():
        # For new users, redirect to billing page to set up a subscription
        if not sub:
            messages.info(request, 'Please set up your subscription to continue.')
            return redirect(reverse('billing:subscribe'))
        # For expired subscriptions
        messages.error(request, 'Your subscription has expired. Please renew to continue.')
        return redirect(reverse('billing:subscription_details'))
    
    # If we get here, user has a valid subscription
    is_trial = False
    if hasattr(sub, 'plan') and sub.plan:
        is_trial = 'trial' in sub.plan.name.lower()

    # Real data metrics (cached)
    cache_ttl = getattr(settings, 'DASHBOARD_CACHE_TTL', 120)
    users_count = cache.get_or_set('dash:users_count', lambda: User.objects.count(), cache_ttl)
    active_subscriptions_count = cache.get_or_set(
        'dash:active_subscriptions_count',
        lambda: Subscription.objects.filter(active=True, end_date__gte=now().date()).count(),
        cache_ttl,
    )
    monthly_revenue = cache.get_or_set(
        'dash:monthly_revenue',
        lambda: (
            Payment.objects.filter(date__year=now().year, date__month=now().month)
            .aggregate(total=Sum('amount')).get('total') or Decimal('0.00')
        ),
        cache_ttl,
    )
    recent_payments = (
        Payment.objects.select_related('user').only('user__email', 'amount', 'date').order_by('-date')[:5]
    )
    recent_users = User.objects.order_by('-date_joined')[:5]
    days_left = (sub.end_date - now().date()).days if sub and sub.end_date else None

    context = {
        'user': request.user,
        'subscription': sub,
        'is_trial': is_trial,
        'users_count': users_count,
        'active_subscriptions_count': active_subscriptions_count,
        'monthly_revenue': monthly_revenue,
        'recent_payments': recent_payments,
        'recent_users': recent_users,
        'days_left': days_left,
        'schema_name': getattr(connection, 'schema_name', 'public'),
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def analytics_view(request):
    today = now().date()
    month_start = today.replace(day=1)

    cache_ttl = getattr(settings, 'ANALYTICS_CACHE_TTL', 300)
    users_total = cache.get_or_set('analytics:users_total', lambda: User.objects.count(), cache_ttl)
    users_new_month = cache.get_or_set(
        'analytics:users_new_month',
        lambda: User.objects.filter(date_joined__date__gte=month_start).count(),
        cache_ttl,
    )
    active_subscriptions = cache.get_or_set(
        'analytics:active_subs',
        lambda: Subscription.objects.filter(active=True, end_date__gte=today).count(),
        cache_ttl,
    )
    revenue_month = cache.get_or_set(
        'analytics:revenue_month',
        lambda: (Payment.objects.filter(date__date__gte=month_start).aggregate(total=Sum('amount')).get('total') or Decimal('0.00')),
        cache_ttl,
    )

    revenue_series = cache.get_or_set(
        'analytics:revenue_series',
        lambda: list(
            Payment.objects.filter(date__date__gte=month_start)
            .annotate(day=TruncDate('date'))
            .values('day')
            .annotate(total=Sum('amount'))
            .order_by('day')
        ),
        cache_ttl,
    )

    signups_series = cache.get_or_set(
        'analytics:signups_series',
        lambda: list(
            User.objects.filter(date_joined__date__gte=month_start)
            .annotate(day=TruncDate('date_joined'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        ),
        cache_ttl,
    )

    context = {
        'users_total': users_total,
        'users_new_month': users_new_month,
        'active_subscriptions': active_subscriptions,
        'revenue_month': revenue_month,
        'revenue_series': revenue_series,
        'signups_series': signups_series,
    }
    return render(request, 'dashboard/analytics.html', context)


@login_required
def export_report_view(request):
    # Simple CSV export for projects and revenue this month
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report.csv"'
    writer = csv.writer(response)

    writer.writerow(["Section", "Metric", "Value"]) 
    # KPIs
    today = now().date()
    month_start = today.replace(day=1)
    revenue_month = (
        Payment.objects.filter(date__date__gte=month_start)
        .aggregate(total=Sum('amount')).get('total') or Decimal('0.00')
    )
    writer.writerow(["KPIs", "Revenue (month)", revenue_month])
    writer.writerow(["KPIs", "Users (total)", User.objects.count()])

    # Projects for user
    writer.writerow([])
    writer.writerow(["Projects for", request.user.email])
    writer.writerow(["Name", "Description", "Created At"]) 
    for p in Project.objects.filter(owner=request.user).order_by('-created_at'):
        writer.writerow([p.name, p.description, p.created_at.isoformat()])

    return response


@login_required
@csrf_protect
def create_project_view(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.tenant_schema_name = getattr(connection, 'schema_name', 'public')
            project.save()
            messages.success(request, 'Project created.')
            return redirect('dashboard:dashboard')
        messages.error(request, 'Please correct the errors in the form.')
    else:
        form = ProjectForm()
    return render(request, 'dashboard/create_project.html', {'form': form})
