from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import UserRole

User = get_user_model()


class AccountsAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testcustomer',
            email='customer@example.com',
            password='Password123!',
            first_name='Anvar',
            last_name='Karimov',
            phone='+998901112233',
            role=UserRole.CUSTOMER
        )
        self.manager = User.objects.create_user(
            username='testmanager',
            email='manager@example.com',
            password='Password123!',
            first_name='Sardor',
            last_name='Aliyev',
            phone='+998909998877',
            role=UserRole.MANAGER
        )

    def test_user_creation_and_roles(self):
        self.assertTrue(self.user.is_customer)
        self.assertFalse(self.user.is_manager)
        self.assertTrue(self.manager.is_manager)
        self.assertFalse(self.manager.is_customer)

    def test_registration_success(self):
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'Botir',
            'last_name': 'Zokirov',
            'phone': '+998901234567',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.role, UserRole.CUSTOMER)
        self.assertEqual(new_user.email, 'newuser@example.com')

    def test_registration_duplicate_email(self):
        url = reverse('accounts:register')
        data = {
            'username': 'anotheruser',
            'email': 'customer@example.com',  # already exists
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='anotheruser').exists())

    def test_login_success(self):
        url = reverse('accounts:login')
        response = self.client.post(url, {
            'username': 'testcustomer',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_invalid(self):
        url = reverse('accounts:login')
        response = self.client.post(url, {
            'username': 'testcustomer',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login yoki parol")

    def test_profile_requires_login(self):
        url = reverse('accounts:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_profile_update(self):
        self.client.login(username='testcustomer', password='Password123!')
        url = reverse('accounts:profile')
        response = self.client.post(url, {
            'action': 'update_profile',
            'first_name': 'Anvarjon',
            'last_name': 'Karimov',
            'email': 'customer@example.com',
            'phone': '+998905554433',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Anvarjon')
        self.assertEqual(self.user.phone, '+998905554433')
