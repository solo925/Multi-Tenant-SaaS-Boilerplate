from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from .models import SystemSetting
from .forms import SystemSettingForm


@login_required
def system_settings_view(request):
    settings_qs = SystemSetting.objects.all().order_by('key')
    form = SystemSettingForm()
    return render(request, 'common/system_settings.html', {
        'settings': settings_qs,
        'form': form,
    })


@login_required
@csrf_protect
def system_settings_create_view(request):
    form = SystemSettingForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Setting created.')
    else:
        messages.error(request, 'Please correct the errors in the form.')
    return redirect('common:system_settings')


@login_required
@csrf_protect
def system_settings_delete_view(request, pk: int):
    try:
        SystemSetting.objects.filter(pk=pk).delete()
        messages.success(request, 'Setting deleted.')
    except Exception:
        messages.error(request, 'Could not delete setting.')
    return redirect('common:system_settings')

from django.shortcuts import render


