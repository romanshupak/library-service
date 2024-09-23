from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user
        if not user.is_staff:
            return Payment.objects.filter(borrowing__user=self.request.user)
        return Payment.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

