import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status, mixins, serializers
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
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

        if borrowing.user != user:
            raise serializers.ValidationError(
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
                success_url=request.build_absolute_uri('/api/payments/success/'),
                cancel_url=request.build_absolute_uri('/api/payments/cancel/'),
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


@csrf_exempt  # Вимкнення перевірки CSRF для вебхука
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return JsonResponse({'status': 'invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'status': 'invalid signature'}, status=400)

    # Обробляємо подію
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Отримання borrowing (збережіть reference_id у session для відстеження)
        borrowing_id = session.get('client_reference_id')  # тут ви повинні зберігати borrowing_id під час створення сесії
        if not borrowing_id:
            return JsonResponse({'status': 'missing reference ID'}, status=400)

        borrowing = get_object_or_404(Borrowing, pk=borrowing_id)

        # # Створення нового запису у таблиці Payment
        # payment = Payment.objects.create(
        #     status=Payment.PaymentStatus.PAID,
        #     borrowing=borrowing,
        #     session_id=session['id'],
        #     money_to_pay=session['amount_total'] / 100,  # конвертація з центів
        #     session_url=session['url']
        # )

        # Оновлення статусу існуючого платежу
        payment = get_object_or_404(Payment, session_id=session['id'])
        payment.status = Payment.PaymentStatus.PAID
        payment.money_to_pay = session['amount_total'] / 100  # конвертація з центів
        payment.session_url = session['url']  # якщо URL змінився
        payment.borrowing = borrowing
        payment.save()  # зберігаємо зміни

    return JsonResponse({'status': 'success'}, status=200)


def success_view(request):
    return JsonResponse({"message": "Payment succeeded!"})


def cancel_view(request):
    return JsonResponse({"message": "Payment was canceled."})
