from django.http import HttpResponseForbidden
from apps.billing.models import Subscription
from datetime import date

def subscription_required(view_func):
    def wrapper(request, *args, **kwargs):
        sub = Subscription.objects.filter(user=request.user, active=True).first()
        if not sub or sub.end_date < date.today():
            return HttpResponseForbidden("Subscription required.")
        return view_func(request, *args, **kwargs)
    return wrapper
