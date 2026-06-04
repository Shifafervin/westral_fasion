from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from user.user_products.models import Cart, CartItem
from user.address_details.models import Address
from admin.admin_orders.models import Order, OrderItem
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import ReturnRequest,ReturnItem
from user.decorators import user_required
from django.db.models import Prefetch
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa
import json
import razorpay
from django.conf import settings
from admin.admin_orders.models import Wallet,WalletTransaction
from decimal import Decimal
from admin.admin_coupon.models import Coupon
from decimal import Decimal
from django.utils.timezone import now
from admin.admin_offers.utils import calculate_discounted_price



@user_required
def checkout_page(request):
    
    active_coupons = Coupon.objects.filter(
        is_active=True,
        is_deleted=False,
        valid_from__lte=now().date(),
        valid_to__gte=now().date()
    )
    selected_payment_method = request.session.get(
    "selected_payment_method",
    "COD"
    )

    selected_address_id = request.session.get(
        "selected_address"
    )

           
    wallet, created = Wallet.objects.get_or_create(

        user=request.user
    )

    cart = Cart.objects.filter(

        user=request.user

    ).first()

    if not cart:

        messages.error(

            request,

            "Your cart is empty"

        )

        return redirect("cart")

    cart_items = CartItem.objects.filter(

        cart=cart

    ).select_related(

        "variant",
        "variant__product"

    ).prefetch_related(

        "variant__images"

    )

    if not cart_items.exists():

        messages.error(

            request,

            "Your cart is empty"

        )

        return redirect("cart")

    subtotal = 0

    checkout_disabled = False

    offer_discount = Decimal("0")

    for item in cart_items:

        item.offer_data = calculate_discounted_price(

            item.variant

        )

        item.subtotal = (

            item.offer_data["final_price"]

            *

            item.quantity

        )

        subtotal += item.subtotal

        offer_discount += (

            item.offer_data["discount_amount"]

            *

            item.quantity

        )

        if (

            item.quantity >

            item.variant.stock

        ):

            checkout_disabled = True

            discount = 0

            applied_coupon = None

            coupon_id = request.session.get(

                "coupon_id"

            )

            if coupon_id:

                applied_coupon = Coupon.objects.filter(

                    id=coupon_id,

                    is_active=True,

                    is_deleted=False

                ).first()

                if applied_coupon:

                    if applied_coupon.discount_type == "Percentage":

                        discount = (

                            subtotal *

                            applied_coupon.discount_value

                        ) / 100

                        if (

                            applied_coupon.maximum_discount_amount

                            and

                            discount >

                            applied_coupon.maximum_discount_amount

                        ):

                            discount = (

                                applied_coupon.maximum_discount_amount

                            )

                    elif applied_coupon.discount_type == "Fixed":

                        discount = (

                            applied_coupon.discount_value

                        )

                    if discount > subtotal:

                        discount = subtotal

    discount = Decimal("0")

    applied_coupon = None

    coupon_id = request.session.get(

        "coupon_id"

    )

    if coupon_id:

        applied_coupon = Coupon.objects.filter(

            id=coupon_id,

            is_active=True,

            is_deleted=False

        ).first()

        if applied_coupon:

            if applied_coupon.discount_type == "Percentage":

                discount = (

                    subtotal *

                    applied_coupon.discount_value

                ) / Decimal("100")

                if (

                    applied_coupon.maximum_discount_amount

                    and

                    discount >

                    applied_coupon.maximum_discount_amount

                ):

                    discount = (

                        applied_coupon.maximum_discount_amount

                    )

            elif applied_coupon.discount_type == "Fixed":

                discount = (

                    applied_coupon.discount_value

                )

            if discount > subtotal:

                discount = subtotal

    shipping_charge = 0

    final_total = (

        subtotal -

        discount +

        shipping_charge

    )
    addresses = Address.objects.filter(

        user=request.user

    ).order_by(

        "-is_default",

        "-created_at"

    )

    selected_address = addresses.filter(

        is_default=True

    ).first()

    context = {

        "cart_items": cart_items,

        "subtotal": subtotal,

        "shipping_charge": shipping_charge,

        "final_total": final_total,

        "addresses": addresses,

        "selected_address": selected_address,

        "checkout_disabled": checkout_disabled,

        "discount": discount,

        "applied_coupon": applied_coupon,

        "wallet": wallet,

        'active_coupons': active_coupons, 

        "selected_payment_method":selected_payment_method,

        "selected_address_id": selected_address_id,

        "offer_discount": offer_discount,

}  

    

    return render(

        request,

        "checkout.html",

        context

    )

@user_required
def place_order(request):

    if request.method != "POST":

        return redirect("checkout_page")

    selected_address_id = request.POST.get(
        "selected_address"
    )

    payment_method = request.POST.get(
        "payment_method"
    )

    # ================= RAZORPAY BLOCK =================

    if payment_method == "RAZORPAY":

        return redirect("checkout_page")

    # ================= ADDRESS VALIDATION =================

    if not selected_address_id:

        messages.error(

            request,

            "Please select an address"

        )

        return redirect("checkout_page")

    address = Address.objects.filter(

        id=selected_address_id,

        user=request.user

    ).first()

    if not address:

        messages.error(

            request,

            "Invalid address selected"

        )

        return redirect("checkout_page")

    # ================= CART =================

    cart = Cart.objects.filter(

        user=request.user

    ).first()

    if not cart:

        messages.error(

            request,

            "Cart not found"

        )

        return redirect("cart")

    cart_items = CartItem.objects.filter(

        cart=cart

    ).select_related(

        "variant",
        "variant__product"

    )

    if not cart_items.exists():

        messages.error(

            request,

            "Your cart is empty"

        )

        return redirect("cart")
    
    

    # ================= TOTAL CALCULATION =================

    subtotal = Decimal("0")

    for item in cart_items:

        if item.quantity > item.variant.stock:

            ...

        offer_data = calculate_discounted_price(

            item.variant

        )

        subtotal += (

            offer_data["final_price"]

            *

            item.quantity

        )

    # ================= COUPON =================

    discount = Decimal("0")

    applied_coupon = None

    coupon_id = request.session.get(

        "coupon_id"

    )

    if coupon_id:

        applied_coupon = Coupon.objects.filter(

            id=coupon_id,

            is_active=True,

            is_deleted=False

        ).first()

        if applied_coupon:

                # Percentage coupon

            if applied_coupon.discount_type == "Percentage":

                discount = (

                    subtotal *

                    applied_coupon.discount_value

                ) / Decimal("100")

                if (

                    applied_coupon.maximum_discount_amount

                    and

                    discount >

                    applied_coupon.maximum_discount_amount

                ):

                    discount = (

                        applied_coupon.maximum_discount_amount

                    )

                # Fixed coupon

            elif applied_coupon.discount_type == "Fixed":

                discount = (

                    applied_coupon.discount_value

                )

                # Prevent negative total

            if discount > subtotal:

                discount = subtotal

        # ================= TOTAL =================

    shipping_charge = Decimal("0")

    final_total = (

        subtotal -

        discount +

        shipping_charge

    )

    if payment_method == "WALLET":

        wallet = Wallet.objects.filter(

            user=request.user

        ).first()

        if not wallet:

            messages.error(

                request,

                "Wallet not found"
            )

            return redirect("checkout_page")

        if wallet.balance < final_total:

            messages.error(

                request,

                "Insufficient wallet balance"
            )

            return redirect("checkout_page")

        wallet.balance -= Decimal(final_total)

        wallet.save()

        wallet_transaction = WalletTransaction.objects.create(

            wallet=wallet,

            transaction_type="Debit",

            status="Completed",

            amount=final_total,

            description="Order Payment"
        )

    offer_discount = Decimal("0")

    for item in cart_items:

        offer_data = calculate_discounted_price(
            item.variant
        )

        offer_discount += (
            offer_data["discount_amount"]
            * item.quantity
        )

    # ================= CREATE ORDER =================

    with transaction.atomic():

        order = Order.objects.create(

            user=request.user,

            total_amount=final_total,

            coupon=applied_coupon,

            coupon_discount=discount,

            payment_method=payment_method,


            offer_discount=offer_discount,

            payment_status=

                "SUCCESS"

                if payment_method == "WALLET"

                else "PENDING",

            order_status="Pending",

            shipping_address=(

                f"{address.full_name}, "

                f"{address.address_line}, "

                f"{address.city}, "

                f"{address.state} - "

                f"{address.pincode}, "

                f"Phone: {address.phone}"

            )

        )
        # ================= REFERRAL REWARD =================

        if (

            request.user.referred_by

            and

            not request.user.referral_reward_given

        ):

            referrer = request.user.referred_by

            wallet, created = Wallet.objects.get_or_create(

                user=referrer

            )

            wallet.balance += Decimal("200")

            wallet.save()

            WalletTransaction.objects.create(

                wallet=wallet,

                transaction_type="Credit",

                status="Completed",

                amount=Decimal("200"),

                description=(
                    f"Referral Reward - "
                    f"{request.user.email}"
                )

            )

            referrer.show_referral_popup = True

            referrer.save()

            request.user.referral_reward_given = True

            request.user.save()

        # ================= ORDER ITEMS =================
        
        for item in cart_items:

            offer_data = calculate_discounted_price(

                item.variant

            )

            item_total = (

                offer_data["final_price"]

                *

                item.quantity

            )

            discount_share = Decimal("0")

            if discount > 0 and subtotal > 0:

                discount_share = (

                    item_total / subtotal

                ) * discount

            OrderItem.objects.create(

                order=order,

                variant=item.variant,

                quantity=item.quantity,

                price_at_purchase=offer_data["final_price"],

                total_price=item_total,

                discount_share=discount_share

            )

            # ================= REDUCE STOCK =================

            item.variant.stock -= item.quantity

            item.variant.save()

        # ================= CLEAR CART =================

        cart_items.delete()
        # ================= UPDATE COUPON USAGE =================

        if applied_coupon:

            applied_coupon.used_count += 1

            applied_coupon.save()
            request.session.pop(

                "coupon_id",

                None

            )

    # ================= SUCCESS =================

    messages.success(

        request,

        "Order placed successfully"

    )

    return redirect(

        "order_success",

        order_id=order.order_id

    )

@user_required
def create_razorpay_order(request):

    if request.method == "POST":

        data = json.loads(request.body)

        amount = int(float(data["amount"]) * 100)

        client = razorpay.Client(

            auth=(

                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET
            )
        )

        payment = client.order.create({

            "amount": amount,
            "currency": "INR",
            "payment_capture": 1

        })

        return JsonResponse({

            "razorpay_order_id": payment["id"],
            "amount": payment["amount"],
            "key": settings.RAZORPAY_KEY_ID

        })
    
@user_required
def payment_success(request):

    razorpay_payment_id = request.GET.get(
        "payment_id"
    )

    razorpay_order_id = request.GET.get(
        "order_id"
    )

    razorpay_signature = request.GET.get(
        "signature"
    )

    address_id = request.GET.get(
        "address_id"
    )

    client = razorpay.Client(

        auth=(

            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    try:

        client.utility.verify_payment_signature({

            "razorpay_order_id":
            razorpay_order_id,

            "razorpay_payment_id":
            razorpay_payment_id,

            "razorpay_signature":
            razorpay_signature

        })

    except:

        messages.error(

            request,

            "Payment verification failed"

        )

        return redirect("checkout_page")

    address = Address.objects.filter(

        id=address_id,
        user=request.user

    ).first()

    if not address:

        messages.error(

            request,

            "Invalid address"

        )

        return redirect("checkout_page")

    cart = Cart.objects.filter(

        user=request.user

    ).first()

    if not cart:

        messages.error(

            request,

            "Cart not found"

        )

        return redirect("cart")

    cart_items = CartItem.objects.filter(

        cart=cart

    ).select_related(

        "variant",
        "variant__product"

    )

    subtotal = Decimal("0")

    for item in cart_items:

        offer_data = calculate_discounted_price(

            item.variant

        )

        subtotal += (

            offer_data["final_price"]

            *

            item.quantity

        )

    discount = Decimal("0")

    applied_coupon = None

    coupon_id = request.session.get(
        "coupon_id"
    )
    if coupon_id:

        applied_coupon = Coupon.objects.filter(

            id=coupon_id,

            is_active=True,

            is_deleted=False

        ).first()

        if applied_coupon:

            if applied_coupon.discount_type == "Percentage":

                discount = (

                    subtotal *

                    applied_coupon.discount_value

                ) / Decimal("100")

                if (

                    applied_coupon.maximum_discount_amount

                    and

                    discount >

                    applied_coupon.maximum_discount_amount

                ):

                    discount = (

                        applied_coupon.maximum_discount_amount

                    )

            elif applied_coupon.discount_type == "Fixed":

                discount = (

                    applied_coupon.discount_value

                )

            if discount > subtotal:

                discount = subtotal


    shipping_charge = 0

    final_total = (

        subtotal -

        discount +

        shipping_charge

    )
    print("SUBTOTAL =", subtotal)
    print("DISCOUNT =", discount)
    print("FINAL TOTAL =", final_total)

    with transaction.atomic():

        order = Order.objects.create(

            user=request.user,

            coupon=applied_coupon,

            total_amount=final_total,

            payment_method="RAZORPAY",

            payment_status="Success",

            order_status="Pending",

            razorpay_order_id=razorpay_order_id,

            razorpay_payment_id=razorpay_payment_id,

            razorpay_signature=razorpay_signature,

            shipping_address=(

                f"{address.full_name}, "

                f"{address.address_line}, "

                f"{address.city}, "

                f"{address.state} - "

                f"{address.pincode}, "

                f"Phone: {address.phone}"

            )

        )

        # ================= REFERRAL REWARD =================

        if (

            request.user.referred_by

            and

            not request.user.referral_reward_given

        ):

            referrer = request.user.referred_by

            wallet, created = Wallet.objects.get_or_create(

                user=referrer

            )

            wallet.balance += Decimal("200")

            wallet.save()

            WalletTransaction.objects.create(

                wallet=wallet,

                transaction_type="Credit",

                status="Completed",

                amount=Decimal("200"),

                description=(
                    f"Referral Reward - "
                    f"{request.user.email}"
                )

            )

            referrer.show_referral_popup = True

            referrer.save()

            request.user.referral_reward_given = True

            request.user.save()

        if applied_coupon:

            applied_coupon.used_count += 1

            applied_coupon.save()

        total_cart_value = subtotal

        for item in cart_items:

            offer_data = calculate_discounted_price(

                item.variant

            )

            item_total = (

                offer_data["final_price"]

                *

                item.quantity

            )

            discount_share = Decimal("0")

            if discount > 0:

                discount_share = (

                    item_total /
                    total_cart_value

                ) * discount

            OrderItem.objects.create(

                order=order,

                variant=item.variant,

                quantity=item.quantity,

                price_at_purchase=offer_data["final_price"],

                total_price=item_total,

                discount_share=discount_share

            )

            item.variant.stock -= item.quantity

            item.variant.save()

        cart_items.delete()

        request.session.pop(
            "coupon_id",
            None
        )

        request.session.pop(
            "selected_payment_method",
            None
        )

        request.session.pop(
            "selected_address",
            None
        )

        return redirect(

            "razorpay_success",

            order_id=order.order_id
        )
    
    
@user_required
def razorpay_success(request, order_id):

    order = Order.objects.filter(

        order_id=order_id,

        user=request.user,

        payment_method="RAZORPAY"

    ).first()

    if not order:

        messages.error(

            request,

            "Razorpay order not found"

        )

        return redirect("home")

    context = {

        "order": order

    }

    return render(

        request,

        "razorpay_success.html",

        context

    )

@user_required
def order_success(request, order_id):

    order = Order.objects.filter(

        order_id=order_id,

        user=request.user

    ).first()

    if not order:

        messages.error(

            request,

            "Order not found"

        )

        return redirect("home")

    context = {

        "order": order

    }

    return render(

        request,

        "order_success.html",

        context

    )


@login_required(login_url='login')
def my_orders(request):

    search = request.GET.get("search", "")
    status = request.GET.get("status", "")

    orders = Order.objects.filter(
        user=request.user
    ).order_by("-created_at")

    if search:

        orders = orders.filter(
            order_id__icontains=search
        )

    if status:

        orders = orders.filter(
            order_status=status
        )

    paginator = Paginator(

        orders,

        6

    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    context = {

        "page_obj": page_obj,
        "search": search,
        "status": status,

    }

    return render(

        request,

        "my_orders.html",

        context

    )

@user_required
def order_detail(request, order_id):

    order = Order.objects.filter(

        order_id=order_id,

        user=request.user

    ).prefetch_related(

        "items",
        "items__variant",
        "items__variant__product",
        "items__variant__images",


        "returns",
        "returns__return_items",
        "returns__return_items__order_item",

    ).first()

    if not order:

        messages.error(

            request,

            "Order not found"

        )

        return redirect(

            "my_orders"
        )

    subtotal = Decimal("0")

    coupon_discount = Decimal("0")

    offer_discount = Decimal("0")

    for item in order.items.all():

        subtotal += item.total_price

        coupon_discount += item.discount_share

        original_total = (

            item.variant.price *

            item.quantity

        )

        offer_discount += (

            original_total -

            item.total_price

        )

    context = {

    "order": order,

    "subtotal": subtotal,

    "coupon_discount": coupon_discount,

    "offer_discount": offer_discount,

}
    return render(

        request,

        "order_detail.html",

        context

    )

@user_required
def cancel_order(request, order_id):

    order = Order.objects.filter(

        order_id=order_id,

        user=request.user

    ).prefetch_related(

        "items",
        "items__variant"

    ).first()

    if not order:

        messages.error(

            request,

            "Order not found"

        )

        return redirect("my_orders")
    
    if order.order_status not in ["Pending", "Processing"]:

        messages.error(

            request,
            "Order can no longer be cancelled"

        )

        return redirect(

            "order_detail",
            order_id=order.order_id
        )

    if order.order_status not in [

        "Pending",

        "Processing"

    ]:

        messages.error(

            request,

            "Order can no longer be cancelled"

        )

        return redirect(

            "order_detail",

            order_id=order.order_id

        )

    if request.method == "POST":

        cancel_reason = request.POST.get(

            "cancel_reason",

            ""

        ).strip()

        with transaction.atomic():

            # RESTORE STOCK

            for item in order.items.all():

                variant = item.variant

                variant.stock += item.quantity

                variant.save()

                item.item_status = "Cancelled"
                
                item.save()


            order.order_status = "Cancelled"

            order.cancel_reason = cancel_reason

            order.cancelled_at = timezone.now()

            order.save()

            if order.payment_method in [

                "RAZORPAY",
                "WALLET"

            ]:

                wallet, created = Wallet.objects.get_or_create(

                    user=request.user
                )

                # ================= DUPLICATE REFUND PROTECTION =================

                existing_refund = WalletTransaction.objects.filter(

                    wallet=wallet,

                    order=order,

                    transaction_type="Credit",

                    description="Order Cancellation Refund"

                ).exists()

                if not existing_refund:

                    wallet.balance += Decimal(

                        order.total_amount
                    )

                    wallet.save()

                    WalletTransaction.objects.create(

                        wallet=wallet,

                        order=order,

                        transaction_type="Credit",

                        status="Completed",

                        amount=order.total_amount,

                        description="Order Cancellation Refund"
                    )

                    order.payment_status = "REFUNDED"

                    order.save()

        messages.success(

            request,

            "Order cancelled successfully"

        )

        return redirect(

            "cancel_success",

            order.order_id

        )

    context = {

        "order": order

    }

    return render(

        request,

        "cancel_order.html",

        context

    )

@user_required
def cancel_success(request, order_id):

    order = Order.objects.filter(

        order_id=order_id,

        user=request.user

    ).first()

    if not order:

        return redirect("my_orders")

    context = {

        "order": order

    }

    return render(

        request,

        "cancel_success.html",

        context

    )


@user_required
@transaction.atomic
def cancel_order_item(request, item_id):

    order_item = OrderItem.objects.select_for_update().filter(

        id=item_id,
        order__user=request.user

    ).select_related(

        "variant",
        "order"

    ).first()

    if not order_item:

        return redirect("my_orders")

    # ALREADY CANCELLED

    if order_item.item_status == "Cancelled":

        messages.warning(

            request,

            "Item already cancelled"

        )

        return redirect(

            "order_detail",

            order_item.order.order_id

        )


    variant = order_item.variant

    variant.stock += order_item.quantity

    variant.save()

    order_item.item_status = "Cancelled"

    order_item.save()

    order = order_item.order

    # ================= WALLET REFUND =================

    if order.payment_method in [

        "RAZORPAY",
        "WALLET"

    ]:

        wallet, created = Wallet.objects.get_or_create(

            user=request.user
        )

        refund_amount = (

            order_item.total_price -

            order_item.discount_share

        )
        # ================= DUPLICATE REFUND PROTECTION =================

        existing_refund = WalletTransaction.objects.filter(

            wallet=wallet,

            order=order,

            amount=refund_amount,

            description="Order Item Cancellation Refund"

        ).exists()

        if not existing_refund:

            wallet.balance += refund_amount

            wallet.save()

            WalletTransaction.objects.create(

                wallet=wallet,

                order=order,

                transaction_type="Credit",

                status="Completed",

                amount=refund_amount,

                description="Order Item Cancellation Refund"
            )
            

    remaining_total = Decimal("0")

    active_items = order.items.exclude(

        item_status="Cancelled"

    )

    for item in active_items:

        remaining_total += (

            item.total_price -

            item.discount_share

        )

    order.total_amount = remaining_total


    if not active_items.exists():

        order.order_status = "Cancelled"

    else:

        if order.order_status == "Cancelled":

            order.order_status = "Processing"

    order.save()

    return JsonResponse({

        "success": True,

        "message": "Item cancelled successfully",

        "item_id": order_item.id,

        "order_cancelled": order.order_status == "Cancelled"

    })


@user_required
def return_order(request, order_id):

    order = Order.objects.filter(

        order_id=order_id,
        user=request.user

    ).first()


    if not order:

        messages.error(

            request,
            "Order not found"

        )

        return redirect("my_orders")


    if order.order_status != "Delivered":

        messages.error(

            request,
            "Only delivered orders can be returned"

        )

        return redirect(

            "order_detail",
            order.order_id

        )


    if request.method == "POST":

        return_reason = request.POST.get(

            "return_reason",
            ""

        ).strip()

        additional_reason = request.POST.get(

            "additional_reason",
            ""

        ).strip()

        selected_items = request.POST.getlist(

            "selected_items"

        )


        if not selected_items:

            messages.error(

                request,
                "Please select at least one item"

            )

            return redirect(

                "return_order",
                order.order_id

            )

        if not return_reason:

            messages.error(

                request,
                "Return reason is required"

            )

            return redirect(

                "return_order",
                order.order_id

            )

    

        return_request = ReturnRequest.objects.create(

            order=order,

            user=request.user,

            reason=return_reason,

            additional_reason=additional_reason

        )

        
        for item_id in selected_items:

            order_item = OrderItem.objects.filter(

                id=item_id,

                order=order

            ).first()

            if order_item:

                # ================= UPDATE ITEM STATUS =================

                order_item.item_status = "Return Requested"

                order_item.save()

                # ================= CREATE RETURN ITEM =================

                ReturnItem.objects.create(

                    return_request=return_request,

                    order_item=order_item,

                    quantity=order_item.quantity,

                    refund_amount=order_item.total_price

                )



        # ================= SUCCESS MESSAGE =================

        messages.success(

            request,
            "Return request submitted successfully"

        )

        # ================= REDIRECT =================

        return redirect(

            "order_detail",
            order_id=order.order_id

        )

    # ================= GET REQUEST =================

    context = {

        "order": order

    }

    return render(

        request,
        "return_order.html",
        context

    )


from decimal import Decimal


@user_required
def invoice_page(request, order_id):

    order = Order.objects.filter(

        order_id=order_id,
        user=request.user

    ).prefetch_related(

        "items",
        "items__variant",
        "items__variant__product",
        "items__variant__images"

    ).first()

    if not order:

        messages.error(

            request,
            "Invoice not found"

        )

        return redirect(

            "my_orders"

        )

    subtotal = Decimal("0")

    coupon_discount = Decimal("0")

    for item in order.items.all():

        subtotal += item.total_price

        coupon_discount += item.discount_share

    context = {

        "order": order,

        "subtotal": subtotal,

        "coupon_discount": coupon_discount,

    }

    return render(

        request,

        "invoice.html",

        context

    )

@user_required
def download_invoice(request, order_id):

    order = Order.objects.filter(

        order_id=order_id,
        user=request.user

    ).prefetch_related(

        "items",
        "items__variant",
        "items__variant__product",
        "items__variant__images"

    ).first()

    if not order:

        messages.error(

            request,
            "Invoice not found"

        )

        return redirect(

            "my_orders"

        )

    template = get_template(
        "invoice_pdf.html"
    )

    html = template.render({

        "order": order

    })

    response = HttpResponse(

        content_type="application/pdf"

    )

    response[

        "Content-Disposition"

    ] = f'attachment; filename="Invoice_{order.order_id}.pdf"'


    pisa_status = pisa.CreatePDF(

        html,
        dest=response
    )

    if pisa_status.err:

        return HttpResponse(

            "Error generating PDF"

        )

    return response

@user_required
def payment_failed(request):

    return render(

        request,

        "payment_failed.html"
    )