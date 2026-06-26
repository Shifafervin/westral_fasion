from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from admin.admin_orders.models import Order
from admin.decorators import admin_required
from user.user_orders.models import ReturnRequest
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.db import transaction
from admin.admin_orders.models import WalletTransaction, Wallet
from decimal import Decimal
import csv
from django.http import HttpResponse


@never_cache
@admin_required
def order_management(request):

    search = request.GET.get("search", "")

    status = request.GET.get("status", "")

    sort = request.GET.get("sort", "latest")

    orders = Order.objects.select_related("user")

    if search:

        orders = orders.filter(
            Q(order_id__icontains=search)
            | Q(user__username__icontains=search)
            | Q(user__email__icontains=search)
        )

    if status:

        orders = orders.filter(order_status=status)

    if sort == "latest":

        orders = orders.order_by("-created_at")

    elif sort == "oldest":

        orders = orders.order_by("created_at")

    elif sort == "high":

        orders = orders.order_by("-total_amount")

    elif sort == "low":

        orders = orders.order_by("total_amount")

    paginator = Paginator(orders, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj, "search": search, "status": status, "sort": sort}

    return render(request, "admin_order_management.html", context)


@never_cache
@admin_required
def admin_order_detail(request, order_id):

    order = (
        Order.objects.filter(order_id=order_id)
        .prefetch_related(
            "items",
            "items__variant",
            "items__variant__product",
            "items__variant__images",
        )
        .select_related("user")
        .first()
    )

    if not order:

        return redirect("order_management")

    context = {"order": order}

    return render(request, "admin_order_detail.html", context)


@require_POST
@admin_required
def update_order_status(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    new_status = request.POST.get("order_status")

    allowed_transitions = {
        "Pending": ["Shipped", "Cancelled"],
        "Shipped": ["Out For Delivery"],
        "Out For Delivery": ["Delivered"],
        "Delivered": [],
        "Cancelled": [],
    }

    current_status = order.order_status

    allowed_next = allowed_transitions.get(current_status, [])

    if new_status in allowed_next:

        with transaction.atomic():

            order.order_status = new_status
            if new_status == "Delivered":

                order.items.filter(
                    item_status="Active"
                ).update(
                    item_status="Delivered"
                )

            elif new_status == "Cancelled":

                order.items.filter(
                    item_status="Active"
                ).update(
                    item_status="Cancelled"
                )

            if (
                new_status == "Delivered"
                and order.payment_method == "COD"
                and order.payment_status == "PENDING"
            ):

                order.payment_status = "SUCCESS"

            order.save()

        messages.success(request, "Order status updated successfully")

    else:

        messages.error(request, "Invalid status transition")

    return redirect("admin_order_detail", order_id=order.order_id)


@never_cache
@admin_required
def return_management(request):

    status_filter = request.GET.get("status", "all")

    search_query = request.GET.get("search", "")

    return_requests = ReturnRequest.objects.select_related("user", "order").order_by(
        "-requested_at"
    )

    if status_filter != "all":

        return_requests = return_requests.filter(status=status_filter)

    if search_query:

        return_requests = return_requests.filter(
            Q(order__order_id__icontains=search_query)
            | Q(user__username__icontains=search_query)
        )

    if request.GET.get("export") == "csv":

        response = HttpResponse(content_type="text/csv")

        response["Content-Disposition"] = 'attachment; filename="return_report.csv"'

        writer = csv.writer(response)

        writer.writerow(
            ["Order ID", "Customer", "Email", "Return Date", "Reason", "Status"]
        )

        for item in return_requests:

            writer.writerow(
                [
                    item.order.order_id,
                    item.user.username,
                    item.user.email,
                    item.requested_at.strftime("%Y-%m-%d"),
                    item.reason,
                    item.status,
                ]
            )

        return response

    paginator = Paginator(return_requests, 6)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "return_requests": page_obj,
        "page_obj": page_obj,
        "status_filter": status_filter,
        "search_query": search_query,
    }

    return render(request, "admin_return_management.html", context)


@require_POST
@admin_required
def approve_return(request, return_id):

    return_request = (
        ReturnRequest.objects.select_related("order", "user")
        .prefetch_related("return_items__order_item__variant")
        .filter(id=return_id)
        .first()
    )
    if not return_request:

        return redirect("return_management")

    if return_request.status != "Pending":

        messages.error(request, "Return status already finalized")

        return redirect("return_management")

    with transaction.atomic():

        wallet, created = Wallet.objects.get_or_create(user=return_request.user)

        return_request.status = "Approved"
        return_request.save()

        order = return_request.order

        refund_amount = Decimal("0")

        for return_item in return_request.return_items.all():

            order_item = return_item.order_item

            item_total = order_item.price_at_purchase * return_item.quantity

            discount_per_unit = order_item.discount_share / order_item.quantity

            refund_amount += item_total - (discount_per_unit * return_item.quantity)

            order_item.variant.stock += return_item.quantity
            order_item.variant.save()

            order_item.item_status = "Return Approved"
            order_item.save()

        if order.payment_method in ["RAZORPAY", "WALLET", "COD"]:

            wallet.balance += refund_amount

            wallet.save()

            WalletTransaction.objects.create(
                wallet=wallet,
                order=return_request.order,
                transaction_type="Credit",
                status="Completed",
                amount=refund_amount,
                description=f"Refund for order {return_request.order.order_id}",
            )

            order.return_status = "Refunded"
            order.payment_status = "REFUNDED"
            order.save()
    messages.success(request, "Return approved and refund added to wallet")
    return redirect("return_management")


@require_POST
@admin_required
def reject_return(request, return_id):

    return_request = (
        ReturnRequest.objects.prefetch_related("return_items__order_item")
        .filter(id=return_id)
        .first()
    )

    if not return_request:

        return redirect("return_management")

    if return_request.status != "Pending":

        messages.error(request, "Return status already finalized")

        return redirect("return_management")

    with transaction.atomic():

        return_request.status = "Rejected"

        return_request.save()

        for return_item in return_request.return_items.all():

            order_item = return_item.order_item

            order_item.item_status = "Return Rejected"

            order_item.save()

    return redirect("return_management")
