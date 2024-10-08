from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from books.models import Book


class PublicBooksApiTests(TestCase):
    def setUp(self):
        """Create test books"""
        self.book_1 = Book.objects.create(
            title="Book One",
            author="Author One",
            cover="hard",
            inventory=10,
            daily_fee=1.50
        )

        self.book_2 = Book.objects.create(
            title="Book Two",
            author="Author Two",
            cover="soft",
            inventory=5,
            daily_fee="2.00"
        )
        self.url = reverse("books:book-list")

    def test_list_books(self):
        """Test retrieving list of books without authentication"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["title"], self.book_1.title)

    def test_retrieve_book(self):
        """Test retrieving exact book without authentication"""
        url = reverse("books:book-detail", args=[self.book_1.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.book_1.title)
        self.assertEqual(response.data["author"], self.book_1.author)


class PrivateBooksApiTests(APITestCase):
    def setUp(self):
        """Preparing for private tests"""
        self.client = APIClient()

        # Create user
        self.user = get_user_model().objects.create_user(
            email="testuser@example.com",
            password="password123"
        )

        # Authenticate created user
        self.client.force_authenticate(user=self.user)

        # Create book
        self.book = Book.objects.create(
            title="Book Three",
            author="Author Three",
            cover="hard",
            inventory=15,
            daily_fee="3.00"
        )
        self.url = reverse("books:book-list")

    def test_create_book(self):
        """Test creation of new book(for authenticated users)"""
        payload = {
            "title": "Book Four",
            "author": "Author Four",
            "cover": "Soft",
            "inventory": 10,
            "daily_fee": "1.75"
        }

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
