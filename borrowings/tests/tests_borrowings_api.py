from datetime import date, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing
from users.models import User


def sample_book(**params):
    """Create and return sample book"""
    defaults = {
        "title": "Sample Book",
        "author": "Sample Author",
        "cover": "hard",
        "inventory": 10,
        "daily_fee": 1.50,
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


def sample_user(**params):
    """Create and return sample user"""
    defaults = {
        "email": "test@email.com",
        "password": "testpassword",
    }
    defaults.update(params)
    return User.objects.create(**defaults)


class PublicBorrowingApiTests(APITestCase):
    def setUp(self):
        """Set up test cases"""
        self.book = sample_book()
        self.borrow_url = reverse("borrowings:borrowing-list")
        self.url = reverse('borrowings:borrowing-list')

    def test_auth_required(self):
        """Test that login is required to fulfill the borrowing request"""
        data = {
            "book_id": self.book.id,
            "borrow_date": "2020-05-21",
            "expected_return_date": "2020-05-30",
            "actual_return_date": "2020-06-05",
        }
        response = self.client.post(self.borrow_url, data)
        self.assertEqual(response.status_code, 401)


class PrivateBorrowingApiTests(APITestCase):
    """Tests for authenticated access to Borrowing API"""

    def setUp(self):
        """Set up authenticated test cases"""
        self.user = sample_user()
        self.client.force_authenticate(user=self.user)
        self.book = sample_book()
        self.borrow_url = reverse("borrowings:borrowing-list")

    def test_create_borrowing_successful(self):
        """Test creating a new borrowing with valid data"""
        data = {
            "book_id": self.book.id,
            "borrow_date": date.today(),
            "expected_return_date": date.today() + timedelta(days=7),
            "user_id": self.user.id
        }
        self.client.force_authenticate(user=self.user)  # Аутентифікація користувача
        response = self.client.post(self.borrow_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 1)
        borrowing = Borrowing.objects.get()
        self.assertEqual(borrowing.book, self.book)
        self.assertEqual(borrowing.user, self.user)

    def test_create_borrowing_invalid(self):
        """Test creating a borrowing with invalid data (missing book)"""
        data = {
            "borrow_date": date.today(),
            "expected_return_date": date.today() + timedelta(days=7),
        }
        response = self.client.post(self.borrow_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_borrowings_list(self):
        """Test retrieving a list of borrowings for authenticated user"""
        Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
        )

        response = self.client.get(self.borrow_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_borrowing_detail(self):
        """Test retrieving a single borrowing by id"""
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
        )
        url = reverse('borrowings:borrowing-detail', args=[borrowing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], borrowing.id)

    def test_delete_borrowing(self):
        """Test deleting a borrowing"""
        borrowing = Borrowing.objects.create(
            book=self.book,
            user=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
        )
        url = reverse('borrowings:borrowing-detail', args=[borrowing.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Borrowing.objects.count(), 0)
