from rest_framework import serializers

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from borrowings.telegram import send_telegram_message


class BorrowingSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(),
        source='book',
        write_only=True
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "book_id",
            "user"
        )

    def validate(self, data):
        """Check if book is available"""
        book = data["book"]
        if book.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock.")
        return data

    def create(self, validated_data):
        """Create borrowing, зменшуємо кількість книг та прив'язуємо поточного користувача"""
        book = validated_data["book"]

        if book.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock.")

        # Зменшуємо кількість книг на 1
        book.inventory -= 1
        book.save()

        # Додаємо поточного користувача до borrowing
        user = self.context["request"].user

        validated_data.pop("user", None)
        borrowing = Borrowing.objects.create(user=user, **validated_data)

        message = (
            f"New borrowing created:\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Borrowing date: {borrowing.borrow_date}\n"
            f"Expected return date: {borrowing.expected_return_date}"
        )

        send_telegram_message(message)

        return borrowing
