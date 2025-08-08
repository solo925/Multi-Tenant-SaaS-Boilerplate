from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Project


class DashboardViewsTests(TestCase):
    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(email="u@example.com", password="pass1234")

    def test_dashboard_redirects_without_subscription(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("dashboard:dashboard"))
        # Without subscription it should redirect to billing subscribe page
        self.assertEqual(resp.status_code, 302)

    def test_analytics_requires_login(self):
        # Unauthenticated
        resp = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(resp.status_code, 302)
        # Authenticated
        self.client.force_login(self.user)
        resp = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(resp.status_code, 200)

    def test_create_project_and_export_report(self):
        self.client.force_login(self.user)
        # Create project
        resp = self.client.post(reverse("dashboard:create_project"), {
            "name": "My Project",
            "description": "Test project",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Project.objects.filter(name="My Project", owner=self.user).exists())
        # Export report
        resp = self.client.get(reverse("dashboard:export_report"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp.headers.get("Content-Type", ""))

# Create your tests here.
