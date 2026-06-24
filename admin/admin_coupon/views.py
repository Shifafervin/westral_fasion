from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Coupon
from .forms import CouponForm
from admin.decorators import admin_required
from django.db.models import Q
import csv
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def coupon_list(request):

    search_query = request.GET.get("search", "")

    status_filter = request.GET.get("status", "all")

    coupons = Coupon.objects.filter(is_deleted=False)

    if search_query:

        coupons = coupons.filter(Q(code__icontains=search_query))

    if status_filter == "active":

        coupons = coupons.filter(is_active=True)

    elif status_filter == "inactive":

        coupons = coupons.filter(is_active=False)

    coupons = coupons.order_by("-created_at")

    if request.GET.get("export") == "csv":

        response = HttpResponse(content_type="text/csv")

        response["Content-Disposition"] = 'attachment; filename="coupons.csv"'

        writer = csv.writer(response)

        writer.writerow(
            [
                "Code",
                "Discount Type",
                "Discount Value",
                "Minimum Purchase",
                "Maximum Discount",
                "Usage Count",
                "Status",
                "Expiry Date",
            ]
        )

        for coupon in coupons:

            writer.writerow(
                [
                    coupon.code,
                    coupon.discount_type,
                    coupon.discount_value,
                    coupon.minimum_purchase_amount,
                    coupon.maximum_discount_amount,
                    coupon.used_count,
                    "Active" if coupon.is_active else "Inactive",
                    coupon.valid_to,
                ]
            )

        return response

    paginator = Paginator(coupons, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
    }

    return render(request, "coupon_list.html", context)


@never_cache
@admin_required
def create_coupon(request):

    if request.method == "POST":

        form = CouponForm(request.POST)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Coupon created successfully."
            )

            return redirect("coupon_list")

    else:

        form = CouponForm()

    return render(request, "add_coupon.html", {"form": form})


@never_cache
@admin_required
def edit_coupon(request, coupon_id):

    coupon = get_object_or_404(Coupon, id=coupon_id, is_deleted=False)

    if request.method == "POST":

        form = CouponForm(request.POST, instance=coupon)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Coupon updated successfully."
            )

            return redirect("coupon_list")
    else:

        form = CouponForm(instance=coupon)

    return render(request, "edit_coupon.html", {"form": form, "coupon": coupon})


@never_cache
@require_POST
@admin_required
def delete_coupon(request, coupon_id):

    coupon = get_object_or_404(Coupon, id=coupon_id, is_deleted=False)

    coupon.is_deleted = True

    Coupon.objects.filter(id=coupon.id).update(is_deleted=True)

    messages.success(request, "Coupon deleted successfully")

    return redirect("coupon_list")


@never_cache
@require_POST
@admin_required
def toggle_coupon_status(request, coupon_id):

    coupon = get_object_or_404(Coupon, id=coupon_id, is_deleted=False)

    coupon.is_active = not coupon.is_active

    coupon.save()

    messages.success(request, "Coupon status updated")

    return redirect("coupon_list")
