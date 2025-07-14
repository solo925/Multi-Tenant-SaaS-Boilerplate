from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Plan, Subscription, Payment
from datetime import timedelta, date
from django.contrib.auth.decorators import login_required

#type: ignore

@login_required
def subscribe_to_plan(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)

    # Cancel any existing subscription
    Subscription.objects.filter(user=request.user).update(active=False)  # type: ignore

    # Create new subscription
    sub = Subscription.objects.create(  # type: ignore
        user=request.user,
        plan=plan,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        active=True
    )  # type: ignore

    messages.success(request, f"You subscribed to {plan.name}")
    return redirect('dashboard')


@login_required
def mock_checkout(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)
    # Here, redirect to Stripe Checkout in real integration
    Payment.objects.create(user=request.user, amount=plan.price, status="paid")  # type: ignore
    messages.success(request, "Payment successful (mock)!")
    return redirect('subscribe', plan_id=plan.id)


def plans_view(request):
    plans = Plan.objects.filter(is_active=True)  # type: ignore
    return render(request, 'billing/plans.html', {'plans': plans})

