from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = [

        "order_id",

        "user",

        "total_amount",

        "order_status",

        "payment_method",

        "payment_status",

        "created_at"

    ]

    search_fields = [

        "order_id",

        "user__username",

        "user__email"

    ]

    list_filter = [

        "order_status",

        "payment_status",

        "payment_method",

        "created_at"

    ]

    ordering = [

        "-created_at"

    ]

    inlines = [

        OrderItemInline

    ]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = [

        "order",

        "variant",

        "quantity",

        "price_at_purchase",

        "total_price"

    ]