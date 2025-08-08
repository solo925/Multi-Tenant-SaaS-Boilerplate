from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Client, Domain
from .forms import CreateTenantForm


class TenantViewsTests(TestCase):
    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="owner@example.com", password="pass1234")

    def test_create_list_and_detail(self):
        self.client.force_login(self.user)
        # Create tenant
        resp = self.client.post(reverse('tenants:create'), {
            'name': 'Tenant X',
            'schema_name': 'tenantx',
            'domain': 'tenantx.localhost',
            'on_trial': True,
        })
        self.assertEqual(resp.status_code, 302)
        client = Client.objects.get(schema_name='tenantx')
        # List
        resp = self.client.get(reverse('tenants:list'))
        self.assertContains(resp, 'Tenant X')
        # Detail
        resp = self.client.get(reverse('tenants:detail', args=[client.pk]))
        self.assertEqual(resp.status_code, 200)
        # Domains actions
        resp = self.client.post(reverse('tenants:domain_add', args=[client.pk]), {
            'domain': 'alt.tenantx.localhost',
            'is_primary': False,
        })
        self.assertEqual(resp.status_code, 302)

# Create your tests here.
