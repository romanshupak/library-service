from rest_framework import serializers
from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from borrowings.telegram import send_telegram_message
from borrowings.utils import create_stripe_session
from payments.serializers import PaymentSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source="book",
        write_only=True
    )
    # Add field to show payments
    payments = PaymentSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "book_id",
            "user",
            "payments",
        )

    def validate(self, data):
        user = self.context["request"].user
        book = data["book"]

        # Checking if book is available
        if book.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock.")

        # Checking if user has an active borrowing
        active_borrowings = Borrowing.objects.filter(
            user=user,
            actual_return_date__isnull=True
        )
        if active_borrowings.exists():
            raise serializers.ValidationError(
                "You already have an active borrowing. "
                "Please return the current book before borrowing a new one."
            )

        return data

    def create(self, validated_data):
        """Create borrowing, decrease amount of books
        and connect current"""
        book = validated_data["book"]

        # Decrease amount of books for 1
        book.inventory -= 1
        book.save()

        # Add current user to borrowing
        user = self.context["request"].user

        validated_data.pop("user", None)
        borrowing = Borrowing.objects.create(user=user, **validated_data)

        # Call func for creation session Stripe
        session = create_stripe_session(borrowing)

        message = (
            f"New borrowing created:\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Borrowing date: {borrowing.borrow_date}\n"
            f"Expected return date: {borrowing.expected_return_date}"
        )

        send_telegram_message(message)

        # Return the borrowing and session URL
        return {
            "borrowing": borrowing,
            "session_url": session.url
        }
