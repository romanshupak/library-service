import logging

import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import viewsets, status, mixins, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from borrowings.models import Borrowing
from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_staff:
            return Payment.objects.filter(borrowing__user=self.request.user)
        return Payment.objects.all()

    def perform_create(self, serializer):
        user = self.request.user

        """ Validate: ensure that user is authorized to create the payment """
        borrowing = serializer.validated_data.get("borrowing")

        if borrowing.user != self.request.user:
            raise ValidationError(
                "You can only create payment for your own borrowing"
            )

        serializer.save(user=self.request.user)


class CreateCheckoutSessionView(APIView):
    """
    Створює Stripe сесію для оплати і повертає URL для переходу на Stripe Checkout.
    """

    def post(self, request, pk):
        # Get Borrowing object by pk
        borrowing = get_object_or_404(Borrowing, pk=pk)
        # Calculate amount to pay
        amount_to_pay = borrowing.calculate_amount_to_pay()
        # Use API key for Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            """ Create Stripe Checkout Session """
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'Book payment {borrowing.book.title}',
                        },
                        'unit_amount': int(amount_to_pay * 100),  # calculate in cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url="http://localhost:8000/api/payments/success/?session_id={CHECKOUT_SESSION_ID}",
                cancel_url="http://localhost:8000/api/payments/cancel/?session_id={CHECKOUT_SESSION_ID}",
                client_reference_id=borrowing.id  # Додаємо borrowing ID
            )
            payment = Payment.objects.create(
                status=Payment.PaymentStatus.PENDING,
                type=Payment.PaymentType.PAYMENT,
                session_url=session.url,
                session_id=session.id,
                money_to_pay=amount_to_pay,
                borrowing=borrowing,
            )

            return Response({"url": session.url}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET_KEY

    logger.info("Received webhook from Stripe")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        logger.info(f"Stripe event constructed successfully: {event['type']}")
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Signature verification failed: {str(e)}")
        return HttpResponse(status=400)

    # Process event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")
        logger.info(f"Processing session ID: {session_id}")

        try:
            payment = Payment.objects.get(session_id=session_id)
            payment.status = Payment.PaymentStatus.PAID
            payment.save()
            logger.info(f"Payment {session_id} updated to PAID.")
            return HttpResponse(status=200)
        except Payment.DoesNotExist:
            logger.error(f"Payment with session ID {session_id} does not exist.")
            return HttpResponse(status=404)

    logger.info("Event processed successfully")
    return HttpResponse(status=200)


class PaymentSuccessView(APIView):
    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "Session ID not provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Отримуємо сесію Stripe для перевірки статусу
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == 'paid':
                # Якщо статус оплати "paid", оновлюємо статус в базі даних
                payment = Payment.objects.get(session_id=session_id)
                payment.status = "success"
                payment.save()

                return Response(
                    {
                        "message": "Payment successful",
                        "session_id": session_id,
                        "status": payment.status,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # Якщо статус не "paid", повертаємо помилку
                return Response(
                    {"error": "Payment not completed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        except stripe.error.StripeError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


def cancel_view(request):
    return JsonResponse(
        {"message": "Payment was canceled."
                    " You can complete the payment later, "
                    "but the session is available for only 24 hours."}
    )
