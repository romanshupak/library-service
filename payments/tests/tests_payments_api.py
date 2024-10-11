from unittest.mock import patch, MagicMock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from payments.models import Payment
from borrowings.models import Borrowing
from django.contrib.auth import get_user_model
import stripe

User = get_user_model()


class PaymentsTests(APITestCase):
    def setUp(self):
        """Create test user"""
        self.user = User.objects.create_user(
            # username='testuser',
            password='password',
            email="test@email.com"
        )
        self.client.force_authenticate(user=self.user)

        """Create test object Borrowings"""
        self.borrowing = Borrowing.objects.create(
            user=self.user,
            book=self.create_test_book(),  # Creation of test book
            borrow_date='2024-10-01',
            expected_return_date='2024-10-10'
        )

    def create_test_book(self):
        from books.models import Book
        return Book.objects.create(
            title="Test Book",
            daily_fee=5.00,
            inventory=10
        )

    def test_create_payment(self):
        url = reverse("payments:payment-create-checkout-session", args=[self.borrowing.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("url", response.data)

        """Check if payment is created"""
        payment = Payment.objects.get(borrowing=self.borrowing)
        self.assertEqual(payment.status, Payment.PaymentStatus.PENDING)
        self.assertEqual(payment.type, Payment.PaymentType.PAYMENT)

    def test_list_payments(self):
        # Створимо кілька платежів для користувача
        Payment.objects.create(
            status=Payment.PaymentStatus.PENDING,
            type=Payment.PaymentType.PAYMENT,
            session_url="http://test.com",
            session_id="test_session_1",
            money_to_pay=50.00,
            borrowing=self.borrowing
        )

        url = reverse("payments:payment-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Має бути 1 платіж для цього користувача

    def test_stripe_webhook_success(self):
        # Створюємо Stripe сесію
        payment = Payment.objects.create(
            status=Payment.PaymentStatus.PENDING,
            type=Payment.PaymentType.PAYMENT,
            session_url="http://test.com",
            session_id="test_session_1",
            money_to_pay=50.00,
            borrowing=self.borrowing
        )

        # Мокаємо Stripe API
        stripe.Webhook.construct_event = lambda *args, **kwargs: {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'test_session_1',
                    'payment_status': 'paid'
                }
            }
        }

        payload = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': payment.session_id,
                    'payment_status': 'paid'
                }
            }
        }

        url = reverse("payments:stripe-webhook")
        response = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Перевіряємо чи статус платежу змінився на PAID
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.PaymentStatus.PAID)

    # def test_payment_success_view(self):
    #     # Створюємо Stripe сесію
    #     payment = Payment.objects.create(
    #         status=Payment.PaymentStatus.PENDING,
    #         type=Payment.PaymentType.PAYMENT,
    #         session_url="http://test.com",
    #         session_id="test_session_1",
    #         money_to_pay=50.00,
    #         borrowing=self.borrowing
    #     )
    #
    #     # Мокаємо Stripe API
    #     stripe.checkout.Session.retrieve = lambda session_id: {
    #         'payment_status': 'paid'
    #     }
    #
    #     url = reverse("payments:payment_success")
    #     response = self.client.get(url, {'session_id': 'test_session_1'})
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #
    #     # Перевіряємо чи статус платежу змінився на success
    #     payment.refresh_from_db()
    #     self.assertEqual(payment.status, Payment.PaymentStatus.PAID)

    def test_payment_success_view(self):
        # Створюємо Stripe сесію
        payment = Payment.objects.create(
            status=Payment.PaymentStatus.PENDING,
            type=Payment.PaymentType.PAYMENT,
            session_url="http://test.com",
            session_id="test_session_1",
            money_to_pay=50.00,
            borrowing=self.borrowing
        )

        # Мокаємо Stripe API
        with patch('stripe.checkout.Session.retrieve') as mock_retrieve:
            # Створюємо мок-об'єкт сесії з необхідними атрибутами
            mock_session = MagicMock()
            mock_session.payment_status = 'paid'
            mock_retrieve.return_value = mock_session

            url = reverse("payments:payment_success")
            response = self.client.get(url, {'session_id': 'test_session_1'})
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Перевіряємо, чи статус платежу змінився на PAID
            payment.refresh_from_db()
            self.assertEqual(payment.status, Payment.PaymentStatus.PAID)
