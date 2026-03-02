from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class UserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {'username': 'testuser', 'email': 'user@test.com', 'password': 'pass1234'}

    def test_register_user(self):
        res = self.client.post('/api/register/', self.user_data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_login_user(self):
        User.objects.create_user(**self.user_data)
        res = self.client.post('/api/api-token-auth/', {'username':'testuser', 'password':'pass1234'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)