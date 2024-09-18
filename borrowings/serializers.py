from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing


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
        """Перевіряємо, чи є книги в наявності"""
        book = data["book"]
        if book.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock.")
        return data

    def create(self, validated_data):
        """Створюємо borrowing, зменшуємо кількість книг та прив'язуємо поточного користувача"""
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

        return borrowing
