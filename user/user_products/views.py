from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from admin.admin_product.models import Product, Variant
from admin.admin_category.models import Category
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Wishlist, WishlistItem
from .models import Cart, CartItem
from django.views.decorators.http import require_POST
from .models import CartItem
from user.decorators import user_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from django.db.models import Sum
from admin.admin_offers.utils import calculate_discounted_price
from .models import Review,ReviewImage
from django.db.models import Avg
from admin.admin_orders.models import OrderItem


def shop(request):

    search = request.GET.get("search", "").strip()

    sort = request.GET.get("sort", "")

    category_id = request.GET.get("category", "")

    min_price = request.GET.get("min_price", "")

    max_price = request.GET.get("max_price", "")

    products = (
        Product.objects.filter(
            is_deleted=False,
            is_active=True,
            category__is_deleted=False,
            category__is_active=True,
        )
        .prefetch_related("variants__images", "category")
        .order_by("-id")
    )

    if search:

        products = products.filter(

            Q(product_name__icontains=search)

            | Q(description__icontains=search)

            | Q(category__category_name__icontains=search)

            | Q(variants__color__icontains=search)

            | Q(variants__size__icontains=search)

            | Q(variants__sku__icontains=search)

        ).distinct()


    if category_id:

        products = products.filter(category_id=category_id)

    product_data = []

    wishlist = None

    if request.user.is_authenticated:

        wishlist = Wishlist.objects.filter(user=request.user).first()


    for product in products:

        default_variant = (
            product.variants.filter(is_deleted=False, is_active=True, is_default=True)
            .prefetch_related("images")
            .first()
        )

        if not default_variant:
            continue

        if min_price:

            try:

                if default_variant.price < float(min_price):
                    continue

            except ValueError:
                pass

        if max_price:

            try:

                if default_variant.price > float(max_price):
                    continue

            except ValueError:
                pass

        primary_image = default_variant.images.filter(is_primary=True).first()

        if not primary_image:

            primary_image = default_variant.images.first()

        in_wishlist = False

        if wishlist:

            in_wishlist = wishlist.items.filter(variant=default_variant).exists()

        available_stock = get_available_stock(default_variant)
        offer_data = calculate_discounted_price(default_variant)
        average_rating = product.reviews.filter(
            is_deleted=False,
            is_visible=True
        ).aggregate(
            Avg("rating")
        )["rating__avg"]

        review_count = product.reviews.filter(
            is_deleted=False,
            is_visible=True
        ).count()

        product_data.append(
            {
                "product": product,
                "variant": default_variant,
                "image": primary_image,
                "in_wishlist": in_wishlist,
                "available_stock": available_stock,
                "offer_data": offer_data,
                "average_rating": average_rating,
                "review_count": review_count,
            }
        )

    if sort == "a-z":

        product_data.sort(key=lambda x: x["product"].product_name.lower())

    elif sort == "z-a":

        product_data.sort(key=lambda x: x["product"].product_name.lower(), reverse=True)

    elif sort == "price-low":

        product_data.sort(key=lambda x: x["variant"].price)

    elif sort == "price-high":

        product_data.sort(key=lambda x: x["variant"].price, reverse=True)

    elif sort == "newest":

        product_data.sort(key=lambda x: x["product"].created_at, reverse=True)

    elif sort == "oldest":

        product_data.sort(key=lambda x: x["product"].created_at)


    paginator = Paginator(product_data, 8)

    page_number = request.GET.get("page")

    products = paginator.get_page(page_number)



    categories = Category.objects.filter(is_deleted=False, is_active=True).order_by(
        "category_name"
    )


    wishlist_count = 0

    if wishlist:

        wishlist_count = wishlist.items.count()

    # ================= CONTEXT =================

    context = {
        "products": products,
        "categories": categories,
        "search": search,
        "sort": sort,
        "category_id": category_id,
        "min_price": min_price,
        "max_price": max_price,
        "wishlist_count": wishlist_count,
    }

    return render(request, "shop.html", context)


@user_required
def toggle_wishlist(request, variant_id):

    variant = get_object_or_404(Variant, id=variant_id)

    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    wishlist_item = wishlist.items.filter(variant=variant).first()

    if wishlist_item:

        wishlist_item.delete()

        wishlist_count = wishlist.items.count()

        return JsonResponse({"status": "removed", "wishlist_count": wishlist_count})

    WishlistItem.objects.create(wishlist=wishlist, variant=variant)

    wishlist_count = wishlist.items.count()

    return JsonResponse({"status": "added", "wishlist_count": wishlist_count})


def product_details(request, product_id):

    product = Product.objects.filter(
        id=product_id,
        is_deleted=False,
        is_active=True,
        category__is_deleted=False,
        category__is_active=True,
    ).first()

    if not product:
        messages.warning(request, "This product is currently unavailable.",)
        return redirect("shop")

    variants = product.variants.filter(
        is_deleted=False, is_active=True
    ).prefetch_related("images")

    if not variants.exists():

        return redirect("shop")

    variant_id = request.GET.get("variant")

    selected_variant = None

    if variant_id:

        selected_variant = variants.filter(id=variant_id).first()

    if not selected_variant:

        selected_variant = variants.filter(is_default=True).first()

    if not selected_variant:

        selected_variant = variants.first()

    images = selected_variant.images.all()

    related_products = Product.objects.filter(
        category=product.category, is_deleted=False, is_active=True
    ).exclude(id=product.id)[:4]

    related_data = []

    for related in related_products:

        related_variant = related.variants.filter(
            is_deleted=False, is_active=True
        ).first()

        if not related_variant:
            continue

        related_image = related_variant.images.filter(is_primary=True).first()

        related_data.append(
            {"product": related, "variant": related_variant, "image": related_image}
        )

    wishlist_count = 0
    in_wishlist = False

    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(
            user=request.user
        ).first()

        if wishlist:

            wishlist_count = wishlist.items.count()

            in_wishlist = WishlistItem.objects.filter(
                wishlist=wishlist,
                variant=selected_variant
            ).exists()

    can_review = False

    if request.user.is_authenticated:

        can_review = OrderItem.objects.filter(
            order__user=request.user,
            order__order_status="Delivered",
            variant__product_id=product.id,
        ).exclude(
            item_status="Cancelled"
        ).exists()
    available_stock = get_available_stock(selected_variant)

    offer_data = calculate_discounted_price(selected_variant)

    reviews = product.reviews.filter(
        is_deleted=False,
        is_visible=True
    ).select_related("user")
    reviews = product.reviews.filter(
        is_deleted=False,
        is_visible=True
    ).prefetch_related(
        "images"
    ).select_related(
        "user"
    )

    average_rating = (
        product.reviews.filter(
            is_deleted=False,
            is_visible=True
        ).aggregate(
            Avg("rating")
        )["rating__avg"]
    )

    review_count = product.reviews.filter(
        is_deleted=False,
        is_visible=True
    ).count()
    edit_review = None

    if request.user.is_authenticated:

        review_id = request.GET.get("edit_review")

        if review_id:

            edit_review = Review.objects.filter(
                id=review_id,
                user=request.user,
                is_deleted=False
            ).first()
    context = {
        "product": product,
        "variants": variants,
        "selected_variant": selected_variant,
        "images": images,
        "related_products": related_data,
        "wishlist_count": wishlist_count,
        "available_stock": available_stock,
        "offer_data": offer_data,
        "reviews": reviews,
        "average_rating": average_rating,
        "review_count": review_count,
        "can_review": can_review,
        "edit_review": edit_review,
        "in_wishlist": in_wishlist,
    }

    return render(request, "product_details.html", context)


@user_required
def add_to_cart(request, variant_id):

    variant = get_object_or_404(
        Variant,
        id=variant_id,
        is_deleted=False,
        is_active=True,
        product__is_deleted=False,
        product__category__is_deleted=False,
        product__category__is_active=True,
    )

    available_stock = get_available_stock(variant)

    if available_stock <= 0:

        return JsonResponse(
            {"success": False, "message": "Product is out of stock"}, status=400
        )

    cart, created = Cart.objects.get_or_create(user=request.user)

    WishlistItem.objects.filter(wishlist__user=request.user, variant=variant).delete()

    cart_item = CartItem.objects.filter(cart=cart, variant=variant).first()

    if cart_item:

        if cart_item.quantity >= 5:

            return JsonResponse(
                {"success": False, "message": "Maximum quantity limit reached"},
                status=400,
            )

        if cart_item.quantity >= available_stock:

            return JsonResponse(
                {"success": False, "message": "Stock limit reached"}, status=400
            )

        cart_item.quantity += 1
        cart_item.save()

    else:

        CartItem.objects.create(cart=cart, variant=variant, quantity=1)

    cart_count = CartItem.objects.filter(cart__user=request.user).count()

    return JsonResponse(
        {"success": True, "message": "Product added to cart", "cart_count": cart_count}
    )


def get_available_stock(variant):

    reserved_quantity = (
        CartItem.objects.filter(variant=variant).aggregate(total=Sum("quantity"))[
            "total"
        ]
        or 0
    )

    return max(0, variant.stock - reserved_quantity)


@user_required
def cart_page(request):

    cart = Cart.objects.filter(user=request.user).first()

    cart_items = []

    subtotal = 0

    total_discount = 0

    checkout_disabled = False

    stock_error = None

    if cart:

        invalid_items = CartItem.objects.filter(cart=cart).filter(
            Q(variant__is_active=False)
            | Q(variant__is_deleted=True)
            | Q(variant__product__is_active=False)
            | Q(variant__product__is_deleted=True)
            | Q(variant__product__category__is_active=False)
        )

        # ================= REMOVE INVALID ITEMS =================

        CartItem.objects.filter(cart=cart).update(is_available=True)

        CartItem.objects.filter(cart=cart).filter(
            Q(variant__is_active=False)
            | Q(variant__is_deleted=True)
            | Q(variant__product__is_active=False)
            | Q(variant__product__is_deleted=True)
            | Q(variant__product__category__is_active=False)
        ).update(is_available=False)

        # ================= FETCH VALID ITEMS =================

        cart_items = (
            CartItem.objects.filter(
                cart=cart,
                variant__is_active=True,
                variant__is_deleted=False,
                variant__product__is_active=True,
                variant__product__is_deleted=False,
                variant__product__category__is_active=True,
            )
            .select_related("variant", "variant__product", "variant__product__category")
            .prefetch_related("variant__images")
        )

        for item in cart_items:

            item.offer_data = calculate_discounted_price(item.variant)

            item.subtotal = item.offer_data["final_price"] * item.quantity

            subtotal += item.subtotal

            total_discount += item.offer_data["discount_amount"] * item.quantity

            if item.quantity > item.variant.stock:

                checkout_disabled = True

                stock_error = (
                    f"{item.variant.product.product_name} "
                    f"has only "
                    f"{item.variant.stock} "
                    f"items left"
                )

    related_products = []

    products = Product.objects.filter(is_deleted=False, is_active=True)[:4]

    for product in products:

        variant = product.variants.filter(is_deleted=False, is_active=True).first()

        if not variant:
            continue

        image = variant.images.filter(is_primary=True).first()

        related_products.append(
            {"product": product, "variant": variant, "image": image}
        )

    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "checkout_disabled": checkout_disabled,
        "stock_error": stock_error,
        "related_products": related_products,
        "total_discount": total_discount,
    }
    return render(request, "cart.html", context)


def get_cart_data(user):

    cart_items = CartItem.objects.filter(cart__user=user).select_related("variant")

    total = 0

    for item in cart_items:

        offer_data = calculate_discounted_price(item.variant)

        total += offer_data["final_price"] * item.quantity

    cart_count = cart_items.count()

    return total, cart_count


@user_required
@require_POST
def increment_cart_item(request, item_id):

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if cart_item.quantity >= 5:

        return JsonResponse(
            {"success": False, "message": "Maximum quantity limit is 5"}, status=400
        )

    available_stock = cart_item.variant.stock

    if cart_item.quantity >= available_stock:

        return JsonResponse(
            {"success": False, "message": f"Only {available_stock} items available"},
            status=400,
        )

    cart_item.quantity += 1
    cart_item.save()

    offer_data = calculate_discounted_price(cart_item.variant)

    subtotal = cart_item.quantity * offer_data["final_price"]

    total, cart_count = get_cart_data(request.user)
    cart_items = CartItem.objects.filter(cart__user=request.user)

    summary_subtotal = 0

    total_discount = 0

    for item in cart_items:

        offer_data = calculate_discounted_price(item.variant)

        summary_subtotal += offer_data["final_price"] * item.quantity

        total_discount += offer_data["discount_amount"] * item.quantity

    return JsonResponse(
        {
            "success": True,
            "message": "Quantity Increase",
            "quantity": cart_item.quantity,
            "subtotal": subtotal,
            "total": total,
            "cart_count": cart_count,
            "stock": cart_item.variant.stock,
            "summary_subtotal": summary_subtotal,
            "total_discount": total_discount,
        }
    )


@user_required
@require_POST
def decrement_cart_item(request, item_id):

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if cart_item.quantity <= 1:
        cart_item.delete()

        total, cart_count = get_cart_data(request.user)
        cart_items = CartItem.objects.filter(cart__user=request.user)

        summary_subtotal = 0

        total_discount = 0

        for item in cart_items:

            offer_data = calculate_discounted_price(item.variant)

            summary_subtotal += offer_data["final_price"] * item.quantity

            total_discount += offer_data["discount_amount"] * item.quantity

        return JsonResponse(
            {
                "success": True,
                "message": "Item removed from cart",
                "quantity": 0,
                "subtotal": 0,
                "total": total,
                "cart_count": cart_count,
                "stock": cart_item.variant.stock,
                "summary_subtotal": summary_subtotal,
                "total_discount": total_discount,
            }
        )

    cart_item.quantity -= 1
    cart_item.save()

    offer_data = calculate_discounted_price(cart_item.variant)

    subtotal = cart_item.quantity * offer_data["final_price"]

    total, cart_count = get_cart_data(request.user)
    cart_items = CartItem.objects.filter(cart__user=request.user)

    summary_subtotal = 0

    total_discount = 0

    for item in cart_items:

        offer_data = calculate_discounted_price(item.variant)

        summary_subtotal += offer_data["final_price"] * item.quantity

        total_discount += offer_data["discount_amount"] * item.quantity

    return JsonResponse(
        {
            "success": True,
            "message": "Quantity Decresed",
            "quantity": cart_item.quantity,
            "subtotal": subtotal,
            "total": total,
            "cart_count": cart_count,
            "stock": cart_item.variant.stock,
            "summary_subtotal": summary_subtotal,
            "total_discount": total_discount,
        }
    )


@user_required
def remove_cart_item(request, item_id):

    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    cart_item.delete()

    messages.success(request, "Product removed to cart", extra_tags="toast")

    return redirect("cart")


@user_required
def add_to_wishlist(request, variant_id):

    variant = get_object_or_404(
        Variant, id=variant_id, is_deleted=False, is_active=True
    )

    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    WishlistItem.objects.get_or_create(wishlist=wishlist, variant=variant)

    messages.success(request, "Added to wishlist", extra_tags="toast")

    return redirect("wishlist")


@user_required
def wishlist_page(request):

    wishlist_items = (
        WishlistItem.objects.filter(
            wishlist__user=request.user,
            variant__is_deleted=False,
            variant__is_active=True,
            variant__product__is_deleted=False,
            variant__product__is_active=True,
            variant__product__category__is_deleted=False,
            variant__product__category__is_active=True,
        )
        .select_related("variant", "variant__product")
        .prefetch_related("variant__images")
    )

    unavailable_items = WishlistItem.objects.filter(wishlist__user=request.user).filter(
        Q(variant__is_deleted=True)
        | Q(variant__is_active=False)
        | Q(variant__product__is_deleted=True)
        | Q(variant__product__is_active=False)
        | Q(variant__product__category__is_deleted=True)
        | Q(variant__product__category__is_active=False)
    )
    for item in wishlist_items:

        item.offer_data = calculate_discounted_price(item.variant)

    context = {
        "wishlist_items": wishlist_items,
        "unavailable_items": unavailable_items,
    }

    return render(request, "wishlist.html", context)


@user_required
def remove_wishlist_item(request, item_id):

    wishlist_item = get_object_or_404(
        WishlistItem, id=item_id, wishlist__user=request.user
    )

    wishlist_item.delete()
    messages.success(request, "Product removed to wishlist", extra_tags="toast")

    return redirect("wishlist")

@login_required
def add_review(request, product_id):

    if request.method != "POST":
        return redirect(
            "product_details",
            product_id=product_id
        )

    product = get_object_or_404(
        Product,
        id=product_id
    )

    rating = request.POST.get("rating")
    comment = request.POST.get("comment")
    image = request.FILES.get("review_image")
    if not rating or not comment:

        messages.error(
            request,
            "Please fill all fields.",
            extra_tags="toast"
        )

        return redirect(
            "product_details",
            product_id=product.id
        )

    purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__order_status="Delivered",
        variant__product_id=product.id,
    ).exclude(
        item_status="Cancelled"
    ).exists()

    if not purchased:

        messages.error(
            request,
            "Only customers who purchased and received this product can review it.",
            extra_tags="toast"
        )

        return redirect(
            "product_details",
            product_id=product.id
        )

    existing_review = Review.objects.filter(
        user=request.user,
        product=product
    ).first()


    if existing_review:

        existing_review.rating = rating
        existing_review.comment = comment
        existing_review.is_deleted = False
        existing_review.save()
        existing_review.images.all().delete()

    
        images = request.FILES.getlist("review_images")

        for image in images[:3]:

            ReviewImage.objects.create(
                review=existing_review,
                image=image
            )

        messages.success(
            request,
            "Review updated successfully.",
            extra_tags="toast"
        )

        return redirect(
            "product_details",
            product_id=product.id
        )

    else:

        review = Review.objects.create(
            user=request.user,
            product=product,
            rating=rating,
            comment=comment,
        )

        images = request.FILES.getlist("review_images")

        for image in images[:3]:

            ReviewImage.objects.create(
                review=review,
                image=image
            )

        messages.success(
            request,
            "Review submitted successfully.",
            extra_tags="toast"
        )

    return redirect(
        "product_details",
        product_id=product.id
    )

@login_required
def delete_review(request, review_id):

    review = get_object_or_404(
        Review,
        id=review_id,
        user=request.user
    )
    
    review.is_deleted = True

    review.save()

    messages.success(
        request,
        "Review deleted successfully.",
        extra_tags="toast"
    )

    return redirect(
        "product_details",
        product_id=review.product.id
    )
    

# @login_required
# def edit_review(request, review_id):

#     review = get_object_or_404(
#         Review,
#         id=review_id,
#         user=request.user,
#         is_deleted=False
#     )

#     if request.method == "POST":

#         review.rating = request.POST.get("rating")

#         review.comment = request.POST.get("comment")

#         review.save()

#         messages.success(
#             request,
#             "Review updated successfully.",
#             extra_tags="toast"
#         )

#     return redirect(
#         "product_details",
#         product_id=review.product.id
#     )