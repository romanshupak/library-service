from django.urls import path, include
from rest_framework import routers

from payments.views import (
    PaymentViewSet,
    CreateCheckoutSessionView,
    stripe_webhook, cancel_view, PaymentSuccessView
)

router = routers.DefaultRouter()
router.register("payments", PaymentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "create_checkout_session/<int:pk>/",
        CreateCheckoutSessionView.as_view(),
        name="payment-create-checkout-session"
    ),
    # path("webhook/", stripe_webhook, name="stripe-webhook"),
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    path("success/", PaymentSuccessView.as_view(), name="payment_success")
    # path("success/", success_view, name="success"),
    # path("cancel/", cancel_view, name="cancel"),
]

app_name = "payments"
