from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from .forms import CreateTenantForm, EditTenantForm, AddDomainForm
from .models import Client, Domain
from django_tenants.utils import tenant_context
from apps.users.models import User
from apps.billing.models import Subscription, Payment
from django.utils.timezone import now
from django.db.models import Sum


@login_required
@csrf_protect
def create_tenant_view(request):
    if request.method == 'POST':
        form = CreateTenantForm(request.POST)
        if form.is_valid():
            client = Client(
                schema_name=form.cleaned_data['schema_name'],
                name=form.cleaned_data['name'],
                on_trial=form.cleaned_data['on_trial'],
            )
            client.save()  # auto_create_schema=True will create the schemas

            Domain.objects.create(
                domain=form.cleaned_data['domain'],
                tenant=client,
                is_primary=True,
            )

            messages.success(request, f"Tenant '{client.name}' created with domain {form.cleaned_data['domain']}")
            return redirect('tenants:list')
    else:
        form = CreateTenantForm()

    return render(request, 'tenants/create_tenant.html', {'form': form})


@login_required
def list_tenants_view(request):
    clients = Client.objects.all().prefetch_related('domains').order_by('-created_on')
    return render(request, 'tenants/list_tenants.html', {
        'clients': clients,
    })


@login_required
def tenant_detail_view(request, pk: int):
    client = get_object_or_404(Client.objects.prefetch_related('domains'), pk=pk)

    # Default metrics
    metrics = {
        'users_count': 0,
        'active_subscriptions_count': 0,
        'monthly_revenue': 0,
    }

    # Try to read tenant-specific stats inside the tenant schema
    try:
        with tenant_context(client):
            metrics['users_count'] = User.objects.count()
            metrics['active_subscriptions_count'] = Subscription.objects.filter(active=True, end_date__gte=now().date()).count()
            metrics['monthly_revenue'] = (
                Payment.objects.filter(date__year=now().year, date__month=now().month)
                .aggregate(total=Sum('amount')).get('total') or 0
            )
    except Exception:
        # If schema tables not present for these apps, ignore metrics
        pass

    return render(request, 'tenants/detail_tenant.html', {
        'tenant': client,
        'metrics': metrics,
        'primary_domain': client.domains.filter(is_primary=True).first(),
        'domains': client.domains.all(),
        'edit_form': EditTenantForm(instance=client),
        'add_domain_form': AddDomainForm(),
    })


@login_required
@csrf_protect
def edit_tenant_view(request, pk: int):
    client = get_object_or_404(Client, pk=pk)
    form = EditTenantForm(request.POST, instance=client)
    if form.is_valid():
        form.save()
        messages.success(request, 'Tenant updated successfully.')
    else:
        messages.error(request, 'Please correct the errors in the form.')
    return redirect('tenants:detail', pk=pk)


@login_required
@csrf_protect
def add_domain_view(request, pk: int):
    client = get_object_or_404(Client, pk=pk)
    form = AddDomainForm(request.POST)
    if form.is_valid():
        domain = Domain.objects.create(
            domain=form.cleaned_data['domain'],
            tenant=client,
            is_primary=False,
        )
        if form.cleaned_data.get('is_primary'):
            Domain.objects.filter(tenant=client).update(is_primary=False)
            domain.is_primary = True
            domain.save(update_fields=['is_primary'])
        messages.success(request, 'Domain added successfully.')
    else:
        messages.error(request, 'Could not add domain. Please check the input.')
    return redirect('tenants:detail', pk=pk)


@login_required
@csrf_protect
def set_primary_domain_view(request, pk: int, domain_id: int):
    client = get_object_or_404(Client, pk=pk)
    domain = get_object_or_404(Domain, pk=domain_id, tenant=client)
    Domain.objects.filter(tenant=client).update(is_primary=False)
    domain.is_primary = True
    domain.save(update_fields=['is_primary'])
    messages.success(request, 'Primary domain updated.')
    return redirect('tenants:detail', pk=pk)


@login_required
@csrf_protect
def delete_domain_view(request, pk: int, domain_id: int):
    client = get_object_or_404(Client, pk=pk)
    domain = get_object_or_404(Domain, pk=domain_id, tenant=client)
    if domain.is_primary and client.domains.exclude(pk=domain.pk).exists():
        messages.error(request, 'Set another domain as primary before deleting this one.')
    else:
        domain.delete()
        messages.success(request, 'Domain deleted.')
    return redirect('tenants:detail', pk=pk)


@login_required
@csrf_protect
def delete_tenant_view(request, pk: int):
    client = get_object_or_404(Client, pk=pk)
    name = client.name
    # WARNING: This does not drop the DB schema. For full cleanup, integrate schema drop if desired.
    client.domains.all().delete()
    client.delete()
    messages.success(request, f"Tenant '{name}' deleted.")
    return redirect('tenants:list')

