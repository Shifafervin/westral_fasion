from django.urls import path
from . import views

urlpatterns = [
    path("apply-coupon/", views.apply_coupon, name="apply_coupon"),
    path("remove-coupon/", views.remove_coupon, name="remove_coupon"),
    path("wallet/", views.wallet_page, name="wallet_page"),
    path(
        "create-wallet-razorpay-order/",
        views.create_wallet_razorpay_order,
        name="create_wallet_razorpay_order",
    ),
    path(
        "wallet-payment-success/",
        views.wallet_payment_success,
        name="wallet_payment_success",
    ),
    path(
        "wallet-payment-failed/",
        views.wallet_payment_failed,
        name="wallet_payment_failed",
    ),
]
