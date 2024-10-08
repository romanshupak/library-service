from django.utils import timezone
from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas import openapi

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer
from borrowings.telegram import send_telegram_message
from borrowings.utils import create_stripe_session, create_stripe_session_for_fine


@extend_schema(
    summary="Retrieve borrowings",
    description="This endpoint allows users to retrieve borrowings. "
                "Non admin users can only view their own borrowings, "
                "while admins can view all borrowings. "
                "Additionally, borrowings can be filtered by 'is_active' "
                "and 'user_id'.",
    request=BorrowingSerializer,
    responses={
        200: BorrowingSerializer(many=True),
    },
)
class BorrowingViewSet(viewsets.ModelViewSet):
    FINE_MULTIPLIER = 2  # Коефіцієнт для розрахунку штрафу

    # queryset = Borrowing.objects.all()
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        """Якщо користувач не адміністратор, показуємо тільки його позичення"""
        if not user.is_staff:
            queryset = Borrowing.objects.filter(user=user)
        else:
            queryset = Borrowing.objects.all()

        """Фільтрація за параметром 'is_active'"""
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)

        """Фільтрація за параметром 'user_id' для адміністраторів"""
        user_id = self.request.query_params.get("user_id")
        if user_id is not None:
            try:
                user_id = int(user_id)
            except ValueError:
                raise ValidationError("Invalid user_id parameter")
            queryset = queryset.filter(user_id=user_id)

        return queryset

    @action(
        detail=True,
        methods=["POST"],
        permission_classes=[IsAuthenticated]
    )
    def return_borrow(self, request, pk=None):
        """Повернення позичення книги"""
        borrowing = self.get_object()

        if borrowing.actual_return_date is not None:
            return Response(
                {"error": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Оновлюємо дату повернення
        borrowing.actual_return_date = timezone.now()
        # borrowing.save()

        # Перевіряємо чи книга повернута вчасно
        expected_return_datetime = timezone.make_aware(
            datetime.combine(
                borrowing.expected_return_date,
                datetime.min.time()
            )
        )

        if borrowing.actual_return_date > expected_return_datetime:
            days_of_overdue = (
                    borrowing.actual_return_date - expected_return_datetime
            ).days

            # Розрахунок суми штрафу
            daily_fee = borrowing.book.daily_fee
            fine_amount = days_of_overdue * daily_fee * self.FINE_MULTIPLIER

            # Створюємо Stripe-сесію для штрафу
            stripe_session = create_stripe_session_for_fine(borrowing, fine_amount)

            # Створюємо платіж за штраф
            borrowing.create_fine_payment(days_of_overdue)
            borrowing.book.inventory += 1
            borrowing.book.save()
            borrowing.save()

            return Response(
                {
                    "message": "The book has been successfully returned with a fine.",
                    "fine_amount": fine_amount,
                    "payment_url": stripe_session['session_url']
                },
                status=status.HTTP_200_OK
            )

        # Оновлюємо дату повернення та збільшуємо inventory +1
        borrowing.book.inventory += 1

        borrowing.book.save()

        borrowing.save()

        return Response(
            {"message": "The book has been successfully returned."},
            status=status.HTTP_200_OK,
        )

    def perform_create(self, serializer):
        """Метод для обробки логіки створення позичання"""
        borrowing = serializer.save()  # Зберігаємо нове позичання
        payment = create_stripe_session(borrowing)  # Створюємо сесію Stripe

        # Якщо сесія була успішно створена, надсилаємо повідомлення в Telegram
        if payment:
            message = (f"Нове позичення:"
                       f" '{borrowing.book.title}' для користувача: "
                       f"{borrowing.user.username}. "
                       f"Оплата: {payment.money_to_pay} USD.")
            send_telegram_message(message)  # Надсилаємо повідомлення в Telegram

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.create(serializer.validated_data)

        return Response(
            {
                "borrowing": result['borrowing'].id,
                "session_url": result['session_url'],  # Повертаємо URL платіжної сесії
            },
            status=status.HTTP_201_CREATED
        )
