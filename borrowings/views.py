from django.utils import timezone
from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
    FINE_MULTIPLIER = 2  # multiplier for fine calculatio

    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        """If user is not admin, show only his borrowings"""
        if not user.is_staff:
            queryset = Borrowing.objects.filter(user=user)
        else:
            queryset = Borrowing.objects.all()

        """Filtration by parameter 'is_active'"""
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)

        """Filtration by parameter 'user_id' for admins"""
        user_id = self.request.query_params.get("user_id")
        if user_id is not None:
            try:
                user_id = int(user_id)
            except ValueError:
                raise ValidationError("Invalid user_id parameter")
            queryset = queryset.filter(user_id=user_id)

        return queryset

    @action(detail=True, methods=["POST"], permission_classes=[IsAuthenticated])
    def return_borrow(self, request, pk=None):
        """Return of book`s borrow"""
        borrowing = self.get_object()

        if borrowing.actual_return_date is not None:
            return Response(
                {"error": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update date of return
        borrowing.actual_return_date = timezone.now()
        # borrowing.save()

        # Check if book returned in time
        expected_return_datetime = timezone.make_aware(
            datetime.combine(borrowing.expected_return_date, datetime.min.time())
        )

        if borrowing.actual_return_date > expected_return_datetime:
            actual_return_date = borrowing.actual_return_date
            overdue_duration = actual_return_date - expected_return_datetime
            days_of_overdue = overdue_duration.days

            # payment for fine amount
            daily_fee = borrowing.book.daily_fee
            fine_amount = days_of_overdue * daily_fee * self.FINE_MULTIPLIER

            # Create Stripe session for fine
            stripe_session = create_stripe_session_for_fine(borrowing, fine_amount)

            # Create payment for fine
            borrowing.create_fine_payment(days_of_overdue)
            borrowing.book.inventory += 1
            borrowing.book.save()
            borrowing.save()

            return Response(
                {
                    "message": "The book has been "
                    "successfully returned with a fine.",
                    "fine_amount": fine_amount,
                    "payment_url": stripe_session["session_url"],
                },
                status=status.HTTP_200_OK,
            )

        # Update date of return and increase inventory +1
        borrowing.book.inventory += 1

        borrowing.book.save()

        borrowing.save()

        return Response(
            {"message": "The book has been successfully returned."},
            status=status.HTTP_200_OK,
        )

    def perform_create(self, serializer):
        """Method for handle of creation borrowing logic"""
        # Save a new borrow and add user
        borrowing = serializer.save(user=self.request.user)
        payment = create_stripe_session(borrowing)  # Create Stripe session

        # If session was successfully created, send message in Telegram
        if payment:
            message = (
                f"New borrow:"
                f" '{borrowing.book.title}' for user: "
                f"{borrowing.user.username}. "
                f"payment: {payment.money_to_pay} USD."
            )
            send_telegram_message(message)  # Send msg in Telegram

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.create(serializer.validated_data)

        return Response(
            {
                "borrowing": result["borrowing"].id,
                # Return URL of stripe session
                "session_url": result["session_url"],
            },
            status=status.HTTP_201_CREATED,
        )
