from decimal import Decimal

import stripe
from django.conf import settings
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_session(borrowing):

    # Use method for calculation of total price
    total_price = Decimal(borrowing.book.daily_fee) * Decimal(
        (borrowing.expected_return_date - borrowing.borrow_date).days
    )

    # Create Stripe session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": borrowing.book.title,
                    },
                    # Stripe uses amount in cents
                    "unit_amount": int(total_price * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        client_reference_id=borrowing.id,
    )

    # Create new payment and connect it to the Borrowing
    Payment.objects.create(
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=total_price,
        status=Payment.PaymentStatus.PENDING,  # Set payment status
        type=Payment.PaymentType.PAYMENT,  # Set payment type
    )

    return session


def create_stripe_session_for_fine(borrowing, fine_amount):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f'Stripe Fine Payment for'
                                f' "{borrowing.book.title}"',
                    },
                    "unit_amount": int(fine_amount * 100),  # in cents
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        client_reference_id=borrowing.id,
    )

    Payment.objects.create(
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=fine_amount,
        status=Payment.PaymentStatus.PENDING,  # Set payment status
        type=Payment.PaymentType.FINE,  # Set payment type
    )

    return {"session_url": session.url, "session_id": session.id}
