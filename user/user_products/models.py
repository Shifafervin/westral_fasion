from django.db import models
from django.conf import settings

from admin.admin_product.models import Variant



# ================= CART MODEL =================

class Cart(models.Model):

    user = models.OneToOneField(

        settings.AUTH_USER_MODEL,

        on_delete=models.CASCADE,

        related_name="cart"

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    updated_at = models.DateTimeField(

        auto_now=True

    )

    def __str__(self):

        return f"{self.user.username} Cart"


# ================= CART ITEM MODEL =================

class CartItem(models.Model):

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    is_available = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    class Meta:

        unique_together = (

            "cart",
            "variant"

        )

    def __str__(self):

        return f"{self.variant.sku} x {self.quantity}"
    

    # ================= WISHLIST MODEL =================

class Wishlist(models.Model):

    user = models.OneToOneField(

    settings.AUTH_USER_MODEL,

        on_delete=models.CASCADE,

        related_name="wishlist"

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    def __str__(self):

        return f"{self.user.username} Wishlist"


# ================= WISHLIST ITEM =================

class WishlistItem(models.Model):

    wishlist = models.ForeignKey(

        Wishlist,

        on_delete=models.CASCADE,

        related_name="items"

    )

    variant = models.ForeignKey(

        Variant,

        on_delete=models.CASCADE

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    class Meta:

        unique_together = (

            "wishlist",
            "variant"

        )

    def __str__(self):

        return self.variant.sku