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

    # Real data metrics
    users_count = User.objects.count()
    active_subscriptions_count = Subscription.objects.filter(active=True, end_date__gte=now().date()).count()
    monthly_revenue = (
        Payment.objects.filter(date__year=now().year, date__month=now().month)
        .aggregate(total=Sum('amount'))
        .get('total')
        or Decimal('0.00')
    )
    recent_payments = (
        Payment.objects.select_related('user').order_by('-date')[:5]
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

    users_total = User.objects.count()
    users_new_month = User.objects.filter(date_joined__date__gte=month_start).count()
    active_subscriptions = Subscription.objects.filter(active=True, end_date__gte=today).count()
    revenue_month = (
        Payment.objects.filter(date__date__gte=month_start)
        .aggregate(total=Sum('amount')).get('total') or Decimal('0.00')
    )

    revenue_series = (
        Payment.objects.filter(date__date__gte=month_start)
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('amount'))
        .order_by('day')
    )

    signups_series = (
        User.objects.filter(date_joined__date__gte=month_start)
        .annotate(day=TruncDate('date_joined'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    context = {
        'users_total': users_total,
        'users_new_month': users_new_month,
        'active_subscriptions': active_subscriptions,
        'revenue_month': revenue_month,
        'revenue_series': list(revenue_series),
        'signups_series': list(signups_series),
    }
    return render(request, 'dashboard/analytics.html', context)
