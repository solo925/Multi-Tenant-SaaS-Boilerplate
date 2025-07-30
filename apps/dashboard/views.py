from apps.billing.models import Subscription
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse

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
        # Check if the plan name contains 'trial' (case-insensitive)
        is_trial = 'trial' in sub.plan.name.lower()
    
    context = {
        'user': request.user,
        'subscription': sub,
        'is_trial': is_trial,
    }
    return render(request, 'dashboard/index.html', context)
