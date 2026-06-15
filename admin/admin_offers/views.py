from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import get_object_or_404

from .models import Offer
from admin.admin_product.models import Product
from admin.admin_category.models import Category

from admin.decorators import admin_required
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def offer_list(request):

    offers = (
        Offer.objects.select_related("product", "category")
        .filter(is_deleted=False)
        .order_by("-created_at")
    )

    search_query = request.GET.get("search", "")

    type_filter = request.GET.get("type", "")

    status_filter = request.GET.get("status", "")

    if search_query:

        offers = offers.filter(
            Q(offer_name__icontains=search_query)
            | Q(product__product_name__icontains=search_query)
            | Q(category__category_name__icontains=search_query)
        )

    if type_filter:

        offers = offers.filter(offer_type=type_filter)

    if status_filter == "active":

        offers = offers.filter(is_active=True)

    elif status_filter == "inactive":

        offers = offers.filter(is_active=False)

    paginator = Paginator(offers, 10)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "type_filter": type_filter,
        "status_filter": status_filter,
        "today": timezone.now(),
    }

    return render(request, "offer_list.html", context)


@never_cache
@admin_required
def add_offer(request):

    products = Product.objects.filter(is_deleted=False)

    categories = Category.objects.filter(is_deleted=False)

    if request.method == "POST":

        offer_name = request.POST.get("offer_name")

        offer_type = request.POST.get("offer_type")

        discount_type = request.POST.get("discount_type")

        discount_value = request.POST.get("discount_value")

        minimum_purchase_amount = request.POST.get("minimum_purchase_amount") or 0

        maximum_discount_amount = request.POST.get("maximum_discount_amount") or 0

        from django.utils import timezone

        start_date = timezone.make_aware(
            datetime.fromisoformat(request.POST.get("start_date"))
        )

        end_date = timezone.make_aware(
            datetime.fromisoformat(request.POST.get("end_date"))
        )

        is_active = request.POST.get("is_active") == "on"

        product = None
        category = None

        if offer_type == "PRODUCT":

            product_id = request.POST.get("product")

            if product_id:

                product = Product.objects.filter(id=product_id).first()

        elif offer_type == "CATEGORY":

            category_id = request.POST.get("category")

            if category_id:

                category = Category.objects.filter(id=category_id).first()

        try:

            offer = Offer(
                offer_name=offer_name,
                offer_type=offer_type,
                discount_type=discount_type,
                discount_value=discount_value,
                minimum_purchase_amount=minimum_purchase_amount,
                maximum_discount_amount=maximum_discount_amount,
                product=product,
                category=category,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
            )

            offer.full_clean()

            offer.save()

            messages.success(request, "Offer created successfully.")

            return redirect("offer_list")

        except ValidationError as e:

            for errors in e.message_dict.values():

                for error in errors:

                    messages.error(request, error)

    context = {"products": products, "categories": categories}

    return render(request, "add_offer.html", context)


@never_cache
@admin_required
def edit_offer(request, offer_id):

    offer = get_object_or_404(Offer, id=offer_id)

    products = Product.objects.filter(is_deleted=False)

    categories = Category.objects.filter(is_deleted=False)

    if request.method == "POST":

        try:

            offer.offer_name = request.POST.get("offer_name")

            offer.offer_type = request.POST.get("offer_type")

            offer.discount_type = request.POST.get("discount_type")

            offer.discount_value = request.POST.get("discount_value")

            offer.minimum_purchase_amount = request.POST.get(
                "minimum_purchase_amount", 0
            )

            offer.maximum_discount_amount = request.POST.get(
                "maximum_discount_amount", 0
            )

            offer.is_active = request.POST.get("is_active") == "on"

            offer.start_date = timezone.make_aware(
                datetime.fromisoformat(request.POST.get("start_date"))
            )

            offer.end_date = timezone.make_aware(
                datetime.fromisoformat(request.POST.get("end_date"))
            )

            if offer.offer_type == "PRODUCT":

                product_id = request.POST.get("product")

                offer.product = Product.objects.filter(id=product_id).first()

                offer.category = None

            else:

                category_id = request.POST.get("category")

                offer.category = Category.objects.filter(id=category_id).first()

                offer.product = None

            offer.full_clean()

            offer.save()

            messages.success(request, "Offer updated successfully.")

            return redirect("offer_list")

        except ValidationError as e:

            for errors in e.message_dict.values():

                for error in errors:

                    messages.error(request, error)

    context = {"offer": offer, "products": products, "categories": categories}

    return render(request, "edit_offer.html", context)


@never_cache
@require_POST
@admin_required
def activate_offer(request, offer_id):

    offer = get_object_or_404(Offer, id=offer_id)

    offer.is_active = True

    offer.save()

    messages.success(request, "Offer activated successfully")

    return redirect("offer_list")


@never_cache
@require_POST
@admin_required
def deactivate_offer(request, offer_id):

    offer = get_object_or_404(Offer, id=offer_id)

    offer.is_active = False

    offer.save()

    messages.success(request, "Offer deactivated successfully")

    return redirect("offer_list")


@never_cache
@require_POST
@admin_required
@admin_required
def delete_offer(request, offer_id):

    offer = get_object_or_404(
        Offer,
        id=offer_id
    )

    offer.delete()

    messages.success(
        request,
        "Offer deleted successfully"
    )

    return redirect(
        "offer_list"
    )