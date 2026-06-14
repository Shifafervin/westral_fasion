from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Category
from .forms import CategoryForm
from django.db import IntegrityError
from django.db.models import Count
from django.core.paginator import Paginator
from admin.decorators import admin_required
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_POST


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def admincategory_view(request):

    # ================= SEARCH =================

    search = request.GET.get("search", "").strip()

    # ================= STATUS FILTER =================

    status = request.GET.get("status", "")

    # ================= QUERYSET =================

    categories = Category.objects.filter(is_deleted=False).annotate(
        product_count=Count("products")
    )

    # ================= SEARCH FILTER =================

    if search:

        categories = categories.filter(category_name__icontains=search)

    # ================= STATUS FILTER =================

    if status == "active":

        categories = categories.filter(is_active=True)

    elif status == "inactive":

        categories = categories.filter(is_active=False)

    # ================= ORDER =================

    categories = categories.order_by("-id")

    # ================= STATS =================

    total_categories = Category.objects.filter(is_deleted=False).count()

    active_categories = Category.objects.filter(
        is_deleted=False, is_active=True
    ).count()

    inactive_categories = Category.objects.filter(
        is_deleted=False, is_active=False
    ).count()

    # ================= PAGINATION =================

    paginator = Paginator(categories, 5)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    # ================= CONTEXT =================

    context = {
        "categories": page_obj,
        "page_obj": page_obj,
        "search": search,
        "selected_status": status,
        "total_categories": total_categories,
        "active_categories": active_categories,
        "inactive_categories": inactive_categories,
    }

    return render(request, "category_management.html", context)


@never_cache
@admin_required
def add_category(request):

    if request.method == "POST":

        form = CategoryForm(request.POST, request.FILES)

        if form.is_valid():

            category = form.save(commit=False)

            category.is_deleted = False

            category.save()

            messages.success(
                request, "Category added successfully", extra_tags="category"
            )

            return redirect("admincategory_view")

        else:

            for field, errors in form.errors.items():

                for error in errors:

                    messages.error(request, error, extra_tags="category")

    else:

        form = CategoryForm()

    context = {"form": form}

    return render(request, "add_category.html", context)


@never_cache
@admin_required
def edit_category(request, id):

    category = get_object_or_404(Category, id=id, is_deleted=False)

    if request.method == "POST":

        form = CategoryForm(request.POST, request.FILES, instance=category)

        if form.is_valid():

            form.save()

            messages.success(
                request, "Category updated successfully", extra_tags="category"
            )

            return redirect("admincategory_view")

        else:

            for field, errors in form.errors.items():

                for error in errors:

                    messages.error(request, error, extra_tags="category")

    else:

        form = CategoryForm(instance=category)

    context = {"form": form, "category": category}

    return render(request, "edit_category.html", context)


@never_cache
@admin_required
def delete_category(request, id):

    category = get_object_or_404(Category, id=id, is_deleted=False)

    if request.method == "POST":

        if category.products.exists():

            messages.error(
                request, "Cannot delete category with products", extra_tags="category"
            )

            return redirect("admincategory_view")

        category.is_deleted = True

        category.save()

        messages.success(
            request, "Category deleted successfully", extra_tags="category"
        )

        return redirect("admincategory_view")

    context = {"category": category}

    return render(request, "delete_category.html", context)


@never_cache
@admin_required
def toggle_category_status(request, id):

    category = get_object_or_404(Category, id=id, is_deleted=False)

    if request.method == "POST":

        category.is_active = not category.is_active

        category.save()
        if category.is_active:

            messages.success(
                request, f"{category.category_name} activated successfully."
            )
        else:

            messages.success(
                request, f"{category.category_name} deactivated successfully."
            )
    return redirect("admincategory_view")
