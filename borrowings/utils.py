from decimal import Decimal

import stripe
from django.conf import settings
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_session(borrowing):

    # Використовуємо метод для обчислення загальної суми
    total_price = borrowing.book.daily_fee * Decimal(
        (borrowing.expected_return_date - borrowing.borrow_date).days
    )

    # Створюємо Stripe сесію
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': borrowing.book.title,
                },
                'unit_amount': int(total_price * 100),  # Stripe використовує суми в центрах
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        client_reference_id=borrowing.id,
    )

    # Створюємо новий платіж і прив'язуємо до Borrowing
    payment = Payment.objects.create(
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        # money_to_pay=total_amount,
        money_to_pay=total_price,
        status=Payment.PaymentStatus.PENDING,  # Встановлюємо статус платежу
        type=Payment.PaymentType.PAYMENT  # Встановлюємо тип платежу
    )

    return session


def create_stripe_session_for_fine(borrowing, fine_amount):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': f'Stripe Fine Payment for "{borrowing.book.title}"',
                },
                'unit_amount': int(fine_amount * 100),  # у центах
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        client_reference_id=borrowing.id
    )

    Payment.objects.create(
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=fine_amount,
        status=Payment.PaymentStatus.PENDING,  # Встановлюємо статус платежу
        type=Payment.PaymentType.FINE  # Встановлюємо тип платежу
    )

    return {
        'session_url': session.url,
        'session_id': session.id
    }
