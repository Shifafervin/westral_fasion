from django.db import models
from django.conf import settings
from admin.admin_product.models import Variant
from django.contrib.auth import get_user_model

User = get_user_model()
from admin.admin_coupon.models import Coupon

# ================= ORDER MODEL =================


class Order(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Shipped", "Shipped"),
        ("Out For Delivery", "Out For Delivery"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS = (
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    )

    PAYMENT_METHODS = (
        ("COD", "Cash on Delivery"),
        ("RAZORPAY", "Razorpay"),
        ("WALLET", "Wallet"),
    )

    RETURN_STATUS = [
        ("Not Requested", "Not Requested"),
        ("Requested", "Requested"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Returned", "Returned"),
        ("Refunded", "Refunded"),
    ]

    return_status = models.CharField(
        max_length=30, choices=RETURN_STATUS, default="Not Requested"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )

    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    offer_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    order_id = models.CharField(max_length=20, unique=True, blank=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    order_status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default="Pending"
    )

    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHODS, default="COD"
    )

    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default="Pending"
    )
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)

    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)

    razorpay_signature = models.TextField(blank=True, null=True)

    shipping_address = models.TextField()

    # ================= CANCELLATION =================

    cancel_reason = models.TextField(null=True, blank=True)

    cancelled_at = models.DateTimeField(null=True, blank=True)

    # ================= TIMESTAMPS =================

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = ["-created_at"]

    def save(self, *args, **kwargs):

        if not self.order_id:

            last_order = Order.objects.exclude(order_id="").order_by("-id").first()

            if last_order and last_order.order_id.startswith("ORD"):

                try:

                    last_id = int(last_order.order_id.replace("ORD", ""))

                    new_id = last_id + 1

                except ValueError:

                    new_id = 1001

            else:

                new_id = 1001

            self.order_id = f"ORD{new_id}"

        super().save(*args, **kwargs)


# ================= ORDER ITEM MODEL =================


class OrderItem(models.Model):

    ITEM_STATUS = [
        ("Active", "Active"),
        ("Cancelled", "Cancelled"),
        ("Returned", "Returned"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()

    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    discount_share = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    item_status = models.CharField(max_length=30, choices=ITEM_STATUS, default="Active")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):

        return f"{self.order.order_id} - " f"{self.variant.sku}"


class Wallet(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


class WalletTransaction(models.Model):

    CREDIT = "Credit"
    DEBIT = "Debit"

    TRANSACTION_TYPES = [(CREDIT, "Credit"), (DEBIT, "Debit")]

    PENDING = "Pending"
    COMPLETED = "Completed"
    FAILED = "Failed"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
    ]

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )

    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL)

    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=COMPLETED)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
