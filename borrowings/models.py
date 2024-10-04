from django.db import models

from books.models import Book
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

        fine_amount = days_of_overdue * self.book.daily_fee * self.FINE_MULTIPLIER

        # Create record for Payment model for fine
        Payment.objects.create(
            status=Payment.PaymentStatus.PAID,
            borrowing=self,
            money_to_pay=fine_amount,
            type=Payment.PaymentType.FINE,
        )
