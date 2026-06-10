from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "product",
        "rating",
        "short_comment",
        "created_at",
    )

    search_fields = (
        "user__username",
        "product__product_name",
        "comment",
    )
    ordering = (
        "-created_at",
    )

    list_filter = (
        "rating",
        "created_at",
    )

    def short_comment(self, obj):

        return obj.comment[:50]

    short_comment.short_description = "Review"