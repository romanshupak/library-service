from django.db import models

from borrowings.models import Borrowing


class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"

    class PaymentType(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(
        max_length=7,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    type = models.CharField(
        max_length=7,
        choices=PaymentType.choices,
    )
    borrowing = models.ForeignKey(Borrowing, on_delete=models.CASCADE)
    session_url = models.URLField()
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"Payment for {self.borrowing.book.title} - {self.get_status_display()}"
