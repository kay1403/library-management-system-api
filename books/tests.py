from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Book, Transaction
import uuid

User = get_user_model()

class BookTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', email='admin@test.com', password='adminpass')
        self.user = User.objects.create_user(username='user', email='user@test.com', password='userpass')
        self.book = Book.objects.create(title="Book1", author="Author1", isbn="1234567890123", published_date="2020-01-01", copies_available=2)
        self.client = APIClient()

    def test_book_list_requires_auth(self):
        res = self.client.get('/api/books/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_book_list_authenticated(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/books/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_checkout_book_success(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/checkout/', {'book_id': self.book.id})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.copies_available, 1)

    import uuid

def test_checkout_book_limit(self):
    self.client.force_authenticate(user=self.user)
    
    for i in range(5):
        b = Book.objects.create(
            title=f"Book{i+2}",
            author=f"Author{i+2}",
            isbn=str(uuid.uuid4()), 
            published_date="2020-01-01",
            copies_available=2
        )
        Transaction.objects.create(user=self.user, book=b)
    
    res = self.client.post('/api/checkout/', {'book_id': self.book.id})
    
    self.assertEqual(res.status_code, 400)
    self.assertIn('Transaction limit reached', res.data['error'])