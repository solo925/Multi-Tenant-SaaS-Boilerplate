from apps.billing.models import Subscription
from django.utils.timezone import now
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    sub = Subscription.objects.filter(user=request.user, active=True).first()  # type: ignore
    if not sub or sub.end_date < now().date():
        return HttpResponseForbidden(b"Your subscription is inactive or expired.")

    return render(request, 'dashboard/index.html')
