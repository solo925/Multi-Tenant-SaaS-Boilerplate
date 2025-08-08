from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Plan, Subscription, Payment


class BillingViewsTests(TestCase):
    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="bill@example.com", password="pass1234")
        self.plan = Plan.objects.create(name="Basic", price=10)

    def test_plans_page(self):
        resp = self.client.get(reverse('billing:plans'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Basic')

    def test_subscribe_flow(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('billing:subscribe', args=[self.plan.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Subscription.objects.filter(user=self.user, plan=self.plan, active=True).exists())

    def test_mock_checkout(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('billing:checkout', args=[self.plan.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Payment.objects.filter(user=self.user, amount=self.plan.price).exists())

# Create your tests here.
