from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        """ If user is not admin, show only his borrowings """
        if not user.is_staff:
            queryset = Borrowing.objects.filter(user=user)
        else:
            queryset = Borrowing.objects.all()

        """" Filtration by param: 'is_active' """
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)

        """" Filtration by param: 'user_id' for admin users """

        user_id = self.request.query_params.get("user_id")
        if user_id is not None:
            try:
                user_id = int(user_id)
            except ValueError:
                raise PermissionDenied("Invalid user_id parameter")

            queryset = queryset.filter(user_id=user_id)

        return queryset
