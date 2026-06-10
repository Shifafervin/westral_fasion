from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.timezone import now
from datetime import timedelta
from .models import Product, Variant, ProductImage
from django.db import transaction
from decimal import Decimal, InvalidOperation
from .forms import ProductForm
from admin.admin_category.models import Category
from .forms import VariantForm
from django.db.models import Sum


def product_management(request):

    search = request.GET.get("search", "").strip()

    category_id = request.GET.get("category")

    status = request.GET.get("status")

    products = (
        Product.objects.filter(
            is_deleted=False, category__is_deleted=False, category__is_active=True
        )
        .prefetch_related("variants", "variants__images")
        .order_by("-id")
    )

    if search:

        products = products.filter(
            Q(product_name__icontains=search) | Q(description__icontains=search)
        )

    if category_id and category_id != "None":

        print("Before Category Filter:", products.count())

        products = products.filter(category_id=category_id)

        print("After Category Filter:", products.count())
        products = products.filter(category_id=category_id)

    if status == "None":
        status = ""
    if status == "active":

        products = products.filter(is_active=True)

    elif status == "inactive":

        products = products.filter(is_active=False)

    total_products = Product.objects.filter(is_deleted=False).count()

    active_products = Product.objects.filter(is_deleted=False, is_active=True).count()

    out_of_stock = (
        Product.objects.filter(is_deleted=False, variants__stock=0).distinct().count()
    )

    new_products = Product.objects.filter(
        created_at__gte=now() - timedelta(days=30), is_deleted=False
    ).count()

    products = products.annotate(total_stock=Sum("variants__stock"))

    paginator = Paginator(products, 4)

    page_number = request.GET.get("page")

    products = paginator.get_page(page_number)

    categories = Category.objects.filter(is_deleted=False, is_active=True)

    context = {
        "products": products,
        "categories": categories,
        "search": search,
        "selected_category": category_id,
        "selected_status": status,
        "total_products": total_products,
        "active_products": active_products,
        "out_of_stock": out_of_stock,
        "new_products": new_products,
    }

    return render(request, "product_management.html", context)


def add_product(request):

    categories = Category.objects.filter(is_active=True, is_deleted=False)

    if request.method == "POST":

        form = ProductForm(request.POST)

        if form.is_valid():

            product = form.save(commit=False)

            product.is_deleted = False

            product.save()

            messages.success(
                request, "Product added successfully", extra_tags="product"
            )

            return redirect("variant_management", product.id)

        else:

            for field, errors in form.errors.items():

                for error in errors:

                    messages.error(request, error, extra_tags="product")

    else:

        form = ProductForm()

    context = {"form": form, "categories": categories}

    return render(request, "add_product.html", context)


def edit_product(request, id):

    product = get_object_or_404(Product, id=id, is_deleted=False)

    categories = Category.objects.filter(is_active=True, is_deleted=False)

    if request.method == "POST":

        form = ProductForm(request.POST, instance=product)

        if form.is_valid():

            form.save()

            messages.success(
                request, "Product updated successfully", extra_tags="product"
            )

            return redirect("product_management")

        else:

            for field, errors in form.errors.items():

                for error in errors:

                    messages.error(request, error, extra_tags="product")

    else:

        form = ProductForm(instance=product)

    context = {"form": form, "product": product, "categories": categories}

    return render(request, "edit_product.html", context)


def delete_product(request, id):

    product = get_object_or_404(Product, id=id, is_deleted=False)

    if request.method == "POST":

        product.is_deleted = True
        product.save()

        messages.success(request, "Product deleted successfully")

        return redirect("product_management")

    context = {"product": product}

    return render(request, "delete_product.html", context)


def toggle_product_status(request, id):

    product = get_object_or_404(Product, id=id, is_deleted=False)

    variant = product.variants.first()

    if variant:

        variant.is_active = not variant.is_active

        variant.save()

    return redirect("product_management")


def variant_management(request, product_id):

    product = get_object_or_404(Product, id=product_id, is_deleted=False)

    search = request.GET.get("search", "").strip()

    variants = (
        product.variants.prefetch_related("images")
        .filter(is_deleted=False)
        .order_by("-id")
    )
    status_filter = request.GET.get("status", "")

    stock_filter = request.GET.get("stock", "")
    if status_filter == "active":

        variants = variants.filter(is_active=True)

    elif status_filter == "disabled":

        variants = variants.filter(is_active=False)

    if stock_filter == "in":

        variants = variants.filter(stock__gt=0)

    elif stock_filter == "out":

        variants = variants.filter(stock=0)

    if search:

        variants = variants.filter(
            Q(color__icontains=search)
            | Q(size__icontains=search)
            | Q(sku__icontains=search)
        )

    all_variants = product.variants.filter(is_deleted=False)

    total_variants = all_variants.count()

    active_variants = all_variants.filter(is_active=True).count()

    out_of_stock = all_variants.filter(stock=0).count()

    default_variant = all_variants.filter(is_default=True).first()

    if not default_variant:

        default_variant = all_variants.first()

    paginator = Paginator(variants, 5)

    page_number = request.GET.get("page")

    variants = paginator.get_page(page_number)

    context = {
        "product": product,
        "variants": variants,
        "search": search,
        "total_variants": total_variants,
        "active_variants": active_variants,
        "out_of_stock": out_of_stock,
        "default_variant": default_variant,
        "status_filter": status_filter,
        "stock_filter": stock_filter,
    }

    return render(request, "varient_management.html", context)


def edit_variant(request, variant_id):

    variant = get_object_or_404(Variant, id=variant_id)

    if request.method == "POST":

        form = VariantForm(request.POST, instance=variant)

        images = [
            request.FILES.get("image1"),
            request.FILES.get("image2"),
            request.FILES.get("image3"),
        ]

        images = [img for img in images if img]

        if images and len(images) < 3:

            messages.error(request, "Minimum 3 images required", extra_tags="variant")

            return render(
                request,
                "edit_varient.html",
                {"variant": variant, "product": variant.product, "form": form},
            )

        if form.is_valid():

            with transaction.atomic():

                updated_variant = form.save(commit=False)

                if updated_variant.is_default:

                    Variant.objects.filter(
                        product=variant.product, is_default=True
                    ).exclude(id=variant.id).update(is_default=False)

                updated_variant.save()

                if images:

                    old_images = list(variant.images.all())

                    for index, image in enumerate(images):

                        if index < len(old_images):

                            old_images[index].image = image

                            old_images[index].save()

                        else:

                            ProductImage.objects.create(
                                variant=variant,
                                image=image,
                                is_primary=True if index == 0 else False,
                            )

            messages.success(
                request, "Variant updated successfully", extra_tags="variant"
            )

            return redirect("variant_management", variant.product.id)

        else:

            for field, errors in form.errors.items():

                for error in errors:

                    messages.error(request, error, extra_tags="variant")

    else:

        form = VariantForm(instance=variant)

    context = {"variant": variant, "product": variant.product, "form": form}

    return render(request, "edit_varient.html", context)


def add_variant(request, product_id):

    product = get_object_or_404(Product, id=product_id, is_deleted=False)

    if request.method == "POST":

        form = VariantForm(request.POST)

        images = [
            request.FILES.get("image1"),
            request.FILES.get("image2"),
            request.FILES.get("image3"),
        ]

        valid_images = [image for image in images if image and image.name]

        if len(valid_images) != 3:

            messages.error(
                request, "Exactly 3 images are required", extra_tags="variant"
            )

            return render(
                request, "add_varient.html", {"product": product, "form": form}
            )

        if form.is_valid():

            with transaction.atomic():

                variant = form.save(commit=False)

                variant.product = product

                if variant.is_default:

                    Variant.objects.filter(product=product, is_default=True).update(
                        is_default=False
                    )

                variant.save()

                for index, image in enumerate(valid_images):

                    ProductImage.objects.create(
                        variant=variant,
                        image=image,
                        is_primary=True if index == 0 else False,
                    )

            messages.success(
                request, "Variant added successfully", extra_tags="variant"
            )

            return redirect("variant_management", product.id)

        else:

            for field, errors in form.errors.items():

                for error in errors:

                    messages.error(request, error, extra_tags="variant")

    else:

        form = VariantForm()

    context = {"product": product, "form": form}

    return render(request, "add_varient.html", context)


def delete_variant_page(request, variant_id):

    variant = get_object_or_404(Variant, id=variant_id, is_deleted=False)

    if request.method == "POST":

        variant.delete()

        return redirect("variant_management", variant.product.id)

    context = {"variant": variant}

    return render(request, "remove_variant.html", context)
