from datetime import timedelta, datetime

from celery import shared_task

from borrowings.models import Borrowing
from borrowings.telegram import send_telegram_message


@shared_task
def check_overdue_borrowings():
    tomorrow = datetime.now() + timedelta(days=1)
    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lte=tomorrow,
        actual_return_date__isnull=True
    )
    for borrowing in overdue_borrowings:
        message = (
            f"Overdue borrowing alert:\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Expected return date: {borrowing.expected_return_date}\n"
            f"Borrow date: {borrowing.borrow_date}"
        )
        send_telegram_message(message)
