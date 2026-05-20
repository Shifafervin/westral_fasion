from django.shortcuts import render, redirect,get_object_or_404

from django.core.paginator import Paginator

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from admin.admin_orders.models import Order
from admin.decorators import admin_required
from user.user_orders.models import ReturnRequest

from django.db.models import Q
from django.contrib import messages
from django.views.decorators.cache import never_cache



@admin_required
def order_management(request):

    # ================= BLOCK NORMAL USERS =================

    if not request.user.is_staff:

        return redirect("home")

    # ================= GET VALUES =================

    search = request.GET.get(

        "search",

        ""

    )

    status = request.GET.get(

        "status",

        ""

    )

    sort = request.GET.get(

        "sort",

        "latest"

    )

    # ================= BASE QUERY =================

    orders = Order.objects.select_related(

        "user"

    )

    # ================= SEARCH =================

    if search:

        orders = orders.filter(

            Q(order_id__icontains=search) |

            Q(user__username__icontains=search) |

            Q(user__email__icontains=search)

        )

    # ================= FILTER =================

    if status:

        orders = orders.filter(

            order_status=status

        )

    # ================= SORT =================

    if sort == "latest":

        orders = orders.order_by(

            "-created_at"

        )

    elif sort == "oldest":

        orders = orders.order_by(

            "created_at"

        )

    elif sort == "high":

        orders = orders.order_by(

            "-total_amount"

        )

    elif sort == "low":

        orders = orders.order_by(

            "total_amount"

        )

    # ================= PAGINATION =================

    paginator = Paginator(

        orders,

        10

    )

    page_number = request.GET.get(

        "page"

    )

    page_obj = paginator.get_page(

        page_number

    )

    # ================= CONTEXT =================

    context = {

        "page_obj": page_obj,

        "search": search,

        "status": status,

        "sort": sort

    }

    return render(

        request,

        "admin_order_management.html",

        context

    )

# ================= ORDER DETAIL =================
@never_cache
@admin_required
def admin_order_detail(request, order_id):

    # ================= BLOCK NORMAL USERS =================

    if not request.user.is_staff:

        return redirect("home")

    order = Order.objects.filter(

        order_id=order_id

    ).prefetch_related(

        "items",
        "items__variant",
        "items__variant__product",
        "items__variant__images"

    ).select_related(

        "user"

    ).first()

    if not order:

        return redirect(

            "order_management"

        )

    context = {

        "order": order

    }

    return render(

        request,

        "admin_order_detail.html",

        context

    )


# ================= UPDATE STATUS =================
@admin_required
def update_order_status(request, order_id):

    order = get_object_or_404(

        Order,
        order_id=order_id

    )

    if request.method == "POST":

        new_status = request.POST.get(

            "order_status"
        )

        allowed_transitions = {

            "Pending": [

                "Shipped",
                "Cancelled"

            ],

            "Shipped": [

                "Out For Delivery"
            ],

            "Out For Delivery": [

                "Delivered"
            ],

            "Delivered": [],

            "Cancelled": []

        }

        current_status = order.order_status

        allowed_next = allowed_transitions.get(

            current_status,
            []
        )

        if new_status in allowed_next:

            order.order_status = new_status

            order.save()

            messages.success(

                request,
                "Order status updated successfully"
            )

        else:

            messages.error(

                request,
                "Invalid status transition"
            )

    return redirect(

        "admin_order_detail",
        order_id=order.order_id
    )



@admin_required
def return_management(request):

    if not request.user.is_staff:

        return redirect("home")

    # ================= GET FILTERS =================

    status_filter = request.GET.get(

        "status",
        "all"

    )

    search_query = request.GET.get(

        "search",
        ""

    )

    # ================= BASE QUERY =================

    return_requests = ReturnRequest.objects.select_related(

        "user",
        "order"

    ).order_by(

        "-requested_at"

    )

    # ================= STATUS FILTER =================

    if status_filter != "all":

        return_requests = return_requests.filter(

            status=status_filter
        )

    # ================= SEARCH =================

    if search_query:

        return_requests = return_requests.filter(

            Q(order__order_id__icontains=search_query) |

            Q(user__username__icontains=search_query)

        )

    # ================= PAGINATION =================

    paginator = Paginator(

        return_requests,
        6

    )

    page_number = request.GET.get(

        "page"
    )

    page_obj = paginator.get_page(

        page_number
    )

    context = {

        "return_requests": page_obj,

        "page_obj": page_obj,

        "status_filter": status_filter,

        "search_query": search_query,

    }

    return render(

        request,

        "admin_return_management.html",

        context

    )

@admin_required
def approve_return(request, return_id):

    if not request.user.is_staff:

        return redirect("home")

    return_request = ReturnRequest.objects.select_related(

        "order",
        "user"

    ).prefetch_related(

        "return_items__order_item__variant"

    ).filter(

        id=return_id

    ).first()
    if return_request.status != "Pending":

        messages.error(

            request,
            "Return status already finalized"

        )

        return redirect("return_management")

    if not return_request:

        return redirect("return_management")

    # ================= ALREADY APPROVED =================

    if return_request.status == "Approved":

        return redirect("return_management")

    # ================= UPDATE RETURN REQUEST =================

    return_request.status = "Approved"

    return_request.save()

    # ================= RETURN ITEMS =================

    for return_item in return_request.return_items.all():

        order_item = return_item.order_item

        # ================= STOCK RESTORE =================

        order_item.variant.stock += return_item.quantity

        order_item.variant.save()

        # ================= ITEM STATUS =================

        order_item.item_status = "Return Approved"

        order_item.save()

    order = return_request.order

    if order.items.exists():

        first_item = order.items.first()

        if return_request.status == "Approved":

            first_item.item_status = "Return Approved"

        elif return_request.status == "Rejected":

            first_item.item_status = "Return Rejected"

        first_item.save()

    return redirect("return_management")

@admin_required
def reject_return(request, return_id):

    if not request.user.is_staff:

        return redirect("home")

    return_request = ReturnRequest.objects.prefetch_related(

        "return_items__order_item"

    ).filter(

        id=return_id

    ).first()

    if not return_request:

        return redirect("return_management")

    # ================= UPDATE RETURN REQUEST =================

    return_request.status = "Rejected"

    return_request.save()

    # ================= UPDATE ITEMS =================

    for return_item in return_request.return_items.all():

        order_item = return_item.order_item

        order_item.item_status = "Return Rejected"

        order_item.save()

    order = return_request.order

    if order.items.exists():

        first_item = order.items.first()

        first_item.item_status = "Return Rejected"

        first_item.save()

    return redirect("return_management")