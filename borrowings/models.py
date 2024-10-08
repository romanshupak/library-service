from django.db import models

from books.models import Book
from borrowings.utils import create_stripe_session_for_fine
from users.models import User


class Borrowing(models.Model):
    FINE_MULTIPLIER = 2

    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowings")

    def __str__(self):
        return f"Borrowing for {self.book.title} by {self.user.email}"

    def calculate_amount_to_pay(self):
        """
        Logic for calculating the amount to pay
         as per amount of days and daily fee
        """
        days_borrowed = (self.expected_return_date - self.borrow_date).days
        daily_rate = self.book.daily_fee
        return days_borrowed * daily_rate

    def create_fine_payment(self, days_of_overdue):
        """
            Creation of fine payment for borrowing
        """
        from payments.models import Payment

        daily_fee = self.book.daily_fee  # Щоденна плата за книгу
        fine_amount = days_of_overdue * daily_fee * self.FINE_MULTIPLIER

        # Створюємо Stripe сесію для оплати штрафу
        payment = create_stripe_session_for_fine(self, fine_amount)

        # Створюємо запис платежу в системі
        Payment.objects.create(
            borrowing=self,
            money_to_pay=fine_amount,
            status=Payment.PaymentStatus.PAID,
            type=Payment.PaymentType.FINE,
            session_url=payment['session_url'],
            session_id=payment['session_id']
        )
