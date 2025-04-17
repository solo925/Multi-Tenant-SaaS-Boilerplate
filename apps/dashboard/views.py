from apps.billing.models import Subscription
from django.utils.timezone import now
from django.http import HttpResponseForbidden

@login_required
def dashboard_view(request):
    sub = Subscription.objects.filter(user=request.user, active=True).first()
    if not sub or sub.end_date < now().date():
        return HttpResponseForbidden("Your subscription is inactive or expired.")

    return render(request, 'dashboard/index.html')
