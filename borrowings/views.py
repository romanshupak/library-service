# from django.utils import timezone
# from rest_framework import viewsets, status
# from rest_framework.decorators import action
# from rest_framework.exceptions import PermissionDenied, ValidationError
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
#
# from borrowings.models import Borrowing
# from borrowings.serializers import BorrowingSerializer
# from borrowings.telegram import send_telegram_message
#
#
# class BorrowingViewSet(viewsets.ModelViewSet):
#     queryset = Borrowing.objects.all()
#     serializer_class = BorrowingSerializer
#     permission_classes = [IsAuthenticated]
#
#     def get_queryset(self):
#         user = self.request.user
#
#         """If user is not admin, show only his borrowings"""
#         if not user.is_staff:
#             queryset = Borrowing.objects.filter(user=user)
#         else:
#             queryset = Borrowing.objects.all()
#
#         """Filtration by param: 'is_active'"""
#         is_active = self.request.query_params.get("is_active")
#         if is_active is not None:
#             if is_active.lower() == "true":
#                 queryset = queryset.filter(actual_return_date__isnull=True)
#             elif is_active.lower() == "false":
#                 queryset = queryset.filter(actual_return_date__isnull=False)
#
#         """Filtration by param: 'user_id' for admin users"""
#
#         user_id = self.request.query_params.get("user_id")
#         if user_id is not None:
#             try:
#                 user_id = int(user_id)
#             except ValueError:
#                 raise PermissionDenied("Invalid user_id parameter")
#
#             queryset = queryset.filter(user_id=user_id)
#
#         return queryset
#
#     def perform_create(self, serializer):
#         user = self.request.user
#         active_borrowings = Borrowing.objects.filter(
#             user=user, actual_return_date__isnull=True
#         )
#
#         if active_borrowings.exists():
#             raise ValidationError(
#                 "You already have an active borrowing. "
#                 "Please return the current book before borrowing a new one."
#             )
#         instance = serializer.save()
#         message = (f"New borrowing created:\nUser: {instance.user.id}\n"
#                    f"User: {instance.user.email}\n"
#                    f"Book: {instance.book.title}")
#         result = send_telegram_message(message)
#         if not result["success"]:
#             print(f"Failed to send Telegram message: {result['message']}")
#
#         payment_view = CreateChekoutSessionView.as_view()
#         request = self.request._request
#         response = payment_view(request, pk=instance.id)
#
#         if response.status_code != 200:
#             instance.delete()
#             raise ValidationError("Failed to create Stripe payment session.")
#         return instance
#
#     @action(
#         detail=True,
#         methods=["POST"],
#         permission_classes=[IsAuthenticated]
#     )
#     def return_borrow(self, request, pk=None):
#         """return borrowing details"""
#         borrowing = self.get_object()
#
#         if borrowing.actual_return_date is not None:
#             return Response(
#                 {"error": "This borrowing has already been returned."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )
#         # Update of actual_return_date, increase amount of books
#
#         borrowing.actual_return_date = timezone.now()
#         borrowing.book.inventory += 1
#         borrowing.book.save()
#         borrowing.save()
#
#         return Response(
#             {"message": "The book has been successfully returned."},
#             status=status.HTTP_200_OK,
#         )

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
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

        # Оновлюємо дату повернення та збільшуємо кількість книг
        borrowing.actual_return_date = timezone.now()
        borrowing.book.inventory += 1
        borrowing.book.save()
        borrowing.save()

        return Response(
            {"message": "The book has been successfully returned."},
            status=status.HTTP_200_OK,
        )
