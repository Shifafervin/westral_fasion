from django.contrib import admin
from .models import Product
from .models import Variant
from .models import ProductImage

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "product_name",
        "category",
        "review_count",
        "is_active",
        "is_deleted",
        "created_at",
    )

    search_fields = (
        "product_name",
    )

    list_filter = (
        "category",
        "is_active",
        "is_deleted",
    )

    ordering = (
        "-created_at",
    )

    def review_count(self, obj):
        return obj.reviews.count()

    review_count.short_description = "Reviews" 


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):

    list_display = (
        "product",
        "size",
        "color",
        "sku",
        "price",
        "stock",
        "is_active",
    )

    search_fields = (
        "sku",
        "product__product_name",
    )

    list_filter = (
        "is_active",
        "color",
        "size",
    )   

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):

    list_display = (
        "variant",
        "is_primary",
        "created_at",
    )

    list_filter = (
        "is_primary",
    )       