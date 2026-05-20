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

@user_required
def checkout_page(request):

    cart = Cart.objects.filter(

        user=request.user

    ).first()

    if not cart:

        messages.error(

            request,

            "Your cart is empty"

        )

        return redirect("cart_page")

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

        return redirect("cart_page")

    subtotal = 0

    checkout_disabled = False

    for item in cart_items:

        item.subtotal = (

            item.variant.price * item.quantity

        )

        subtotal += item.subtotal

        if (

            item.quantity >

            item.variant.stock

        ):

            checkout_disabled = True

    shipping_charge = 0

    final_total = (

        subtotal + shipping_charge
    )

    discount = 0
    final_total = subtotal - discount + shipping_charge

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

        "discount": discount

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

    print(
        "SELECTED ADDRESS ID :",
        selected_address_id
    )

    payment_method = request.POST.get(
        "payment_method"
    )

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

    cart = Cart.objects.filter(

        user=request.user

    ).first()

    if not cart:

        messages.error(

            request,

            "Cart not found"

        )

        return redirect("cart_page")

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

        return redirect("cart_page")

    subtotal = 0

    for item in cart_items:

        if item.quantity > item.variant.stock:

            messages.error(

                request,

                f"{item.variant.product.product_name} is out of stock"

            )

            return redirect("checkout_page")

        subtotal += (

            item.variant.price *
            item.quantity

        )

    shipping_charge = 0

    final_total = (

        subtotal + shipping_charge
    )

    with transaction.atomic():

        order = Order.objects.create(

            user=request.user,

            total_amount=final_total,

            payment_method=payment_method,

            payment_status="Pending",

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

        for item in cart_items:

            OrderItem.objects.create(

                order=order,

                variant=item.variant,

                quantity=item.quantity,

                price_at_purchase=item.variant.price,

                total_price=(

                    item.variant.price *
                    item.quantity

                )

            )

            item.variant.stock -= item.quantity

            item.variant.save()

        cart_items.delete()

    messages.success(

        request,

        "Order placed successfully"

    )

    return redirect(

        "order_success",

        order.order_id

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

        4

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

        # ================= RETURN ITEMS =================

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

    context = {

        "order": order

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

            # UPDATE ORDER

            order.order_status = "Cancelled"

            order.cancel_reason = cancel_reason

            order.cancelled_at = timezone.now()

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

    # RESTORE STOCK

    variant = order_item.variant

    variant.stock += order_item.quantity

    variant.save()

    # CANCEL ITEM

    order_item.item_status = "Cancelled"

    order_item.save()

    order = order_item.order

    # RECALCULATE TOTAL

    remaining_total = 0

    active_items = order.items.exclude(

        item_status="Cancelled"

    )

    for item in active_items:

        remaining_total += item.total_price

    order.total_amount = remaining_total

    # FULL ORDER CANCEL

    if not active_items.exists():

        order.order_status = "Cancelled"

    else:

        # OPTIONAL SAFETY
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

    # ================= ORDER NOT FOUND =================

    if not order:

        messages.error(

            request,
            "Order not found"

        )

        return redirect("my_orders")

    # ================= ONLY DELIVERED ORDERS =================

    if order.order_status != "Delivered":

        messages.error(

            request,
            "Only delivered orders can be returned"

        )

        return redirect(

            "order_detail",
            order.order_id

        )

    # ================= FORM SUBMIT =================

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

        # ================= VALIDATIONS =================

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

        # ================= CREATE RETURN REQUEST =================

        # ================= CREATE RETURN REQUEST =================

        return_request = ReturnRequest.objects.create(

            order=order,

            user=request.user,

            reason=return_reason,

            additional_reason=additional_reason

        )

        # ================= RETURN ITEMS =================

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

    context = {

        "order": order

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