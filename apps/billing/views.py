from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Plan, Subscription
from datetime import timedelta, date

@login_required
def subscribe_to_plan(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)

    # Cancel any existing subscription
    Subscription.objects.filter(user=request.user).update(active=False)

    # Create new subscription
    sub = Subscription.objects.create(
        user=request.user,
        plan=plan,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        active=True
    )

    messages.success(request, f"You subscribed to {plan.name}")
    return redirect('dashboard')


@login_required
def mock_checkout(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)
    # Here, redirect to Stripe Checkout in real integration
    Payment.objects.create(user=request.user, amount=plan.price, status="paid")
    messages.success(request, "Payment successful (mock)!")
    return redirect('subscribe', plan_id=plan.id)

