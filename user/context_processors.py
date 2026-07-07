from user.user_products.models import CartItem, WishlistItem

def navbar_counts(request):
    cart_count = 0
    wishlist_count = 0

    if request.user.is_authenticated:

        cart_count = CartItem.objects.filter(
            cart__user=request.user
        ).count()

        wishlist_count = WishlistItem.objects.filter(
            wishlist__user=request.user,
            variant__is_deleted=False,
            variant__is_active=True,
            variant__product__is_deleted=False,
            variant__product__is_active=True,
            variant__product__category__is_deleted=False,
            variant__product__category__is_active=True,
        ).count()

    return {
        "cart_count": cart_count,
        "wishlist_count": wishlist_count,
    }