from django.urls import path
from . import views

urlpatterns = [
    path("checkout/", views.checkout_page, name="checkout_page"),
    path("place-order/", views.place_order, name="place_order"),
    path("order-success/<str:order_id>/", views.order_success, name="order_success"),
    path("my-orders/", views.my_orders, name="my_orders"),
    path("order-detail/<str:order_id>/", views.order_detail, name="order_detail"),
    path("cancel-order/<str:order_id>/", views.cancel_order, name="cancel_order"),
    path("cancel-success/<str:order_id>/", views.cancel_success, name="cancel_success"),
    path(
        "cancel-order-item/<int:item_id>/",
        views.cancel_order_item,
        name="cancel_order_item",
    ),
    path("return-order/<str:order_id>/", views.return_order, name="return_order"),
    path("invoice/<str:order_id>/", views.invoice_page, name="invoice_page"),
    path(
        "download-invoice/<str:order_id>/",
        views.download_invoice,
        name="download_invoice",
    ),
    path(
        "create-razorpay-order/",
        views.create_razorpay_order,
        name="create_razorpay_order",
    ),
    path("payment-success/", views.payment_success, name="payment_success"),
    path(
        "razorpay-success/<str:order_id>/",
        views.razorpay_success,
        name="razorpay_success",
    ),
    path("payment-failed/", views.payment_failed, name="payment_failed"),
]
