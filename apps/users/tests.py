from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


class AuthViewsTests(TestCase):
    def setUp(self) -> None:
        self.User = get_user_model()

    def test_register_and_login(self):
        # Register
        resp = self.client.post(reverse('register'), {
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.User.objects.filter(email='new@example.com').exists())
        # Logout
        self.client.get(reverse('logout'))
        # Login
        resp = self.client.post(reverse('login'), {
            'username': 'new@example.com',
            'password': 'StrongPass123!',
        })
        self.assertEqual(resp.status_code, 302)

# Create your tests here.
