from django.db import models
from admin.admin_orders.models import Order,OrderItem
from django.conf import settings
from admin.admin_orders.models import OrderItem


class ReturnRequest(models.Model):

    RETURN_STATUS = (

        ("Pending", "Pending"),

        ("Approved", "Approved"),

        ("Rejected", "Rejected"),

        ("Refunded", "Refunded"),

    )

    REFUND_METHOD = (

        ("Original Payment", "Original Payment"),

        ("Wallet", "Wallet"),

    )

    order = models.ForeignKey(

        Order,

        on_delete=models.CASCADE,

        related_name="returns"

    )

    user = models.ForeignKey(

        settings.AUTH_USER_MODEL,   

        on_delete=models.CASCADE

    )

    reason = models.CharField(

        max_length=255

    )

    additional_reason = models.TextField(

        blank=True,

        null=True

    )

    refund_method = models.CharField(

        max_length=50,

        choices=REFUND_METHOD,

        default="Wallet"

    )

    status = models.CharField(

        max_length=30,

        choices=RETURN_STATUS,

        default="Pending"

    )

    requested_at = models.DateTimeField(

        auto_now_add=True

    )

    updated_at = models.DateTimeField(

        auto_now=True

    )

    admin_note = models.TextField(

        blank=True,

        null=True

    )

    refunded_at = models.DateTimeField(

        blank=True,

        null=True

    )

    def __str__(self):

        return f"{self.order.order_id} - {self.status}"
    

class ReturnItem(models.Model):


    return_request = models.ForeignKey(

        ReturnRequest,

        on_delete=models.CASCADE,

        related_name="return_items"

    )

    order_item = models.ForeignKey(

        OrderItem,

        on_delete=models.CASCADE,

        related_name="returns",

        null=True,

        blank=True

    )

    quantity = models.PositiveIntegerField(

        default=1

    )

    refund_amount = models.DecimalField(

        max_digits=10,

        decimal_places=2

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    def __str__(self):

        return (

            f"{self.return_request.order.order_id}"

            f" - "

            f"{self.order_item.variant.product.product_name}"

        )