from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from admin.admin_category.models import Category
from admin.admin_product.models import Product
import re


class Offer(models.Model):

    OFFER_TYPE_CHOICES = (
        ("PRODUCT", "Product"),
        ("CATEGORY", "Category"),
    )

    DISCOUNT_TYPE_CHOICES = (
        ("PERCENTAGE", "Percentage"),
        ("FLAT", "Flat"),
    )

    offer_name = models.CharField(max_length=100)

    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES)

    discount_type = models.CharField(
        max_length=20, choices=DISCOUNT_TYPE_CHOICES, default="PERCENTAGE"
    )

    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    minimum_purchase_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    maximum_discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True
    )

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True
    )

    start_date = models.DateTimeField()

    end_date = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    is_deleted = models.BooleanField(default=False)

    def clean(self):

        if not re.match(r"^[A-Za-z0-9 %\-]+$", self.offer_name.strip()):

            raise ValidationError(
                {
                    "offer_name": "Offer name can contain only letters, numbers and spaces."
                }
            )

        if self.offer_type == "PRODUCT":

            if not self.product:

                raise ValidationError({"product": "Please select a product."})

            self.category = None

        elif self.offer_type == "CATEGORY":

            if not self.category:

                raise ValidationError({"category": "Please select a category."})

            self.product = None

        if self.end_date <= self.start_date:

            raise ValidationError({"end_date": "End date must be after start date."})

        if self.end_date.date() < timezone.now().date():

            raise ValidationError({"end_date": "End date cannot be in the past."})

        if self.discount_value <= 0:

            raise ValidationError(
                {"discount_value": "Discount value must be greater than 0."}
            )

        if self.discount_type == "PERCENTAGE":

            if self.discount_value > 50:

                raise ValidationError(
                    {"discount_value": "Percentage offer cannot exceed 50%."}
                )

            if self.maximum_discount_amount <= 0:

                raise ValidationError(
                    {
                        "maximum_discount_amount": "Maximum discount amount is required for percentage offers."
                    }
                )

        if self.discount_type == "FLAT":

            if self.discount_value > 300:

                raise ValidationError(
                    {"discount_value": "Flat offer cannot exceed ₹300."}
                )

            if (
                self.maximum_discount_amount > 0
                and self.minimum_purchase_amount > 0
                and self.maximum_discount_amount > self.minimum_purchase_amount
            ):
                raise ValidationError(
                    {
                        "maximum_discount_amount": "Maximum discount cannot exceed minimum purchase amount."
                    }
                )

        if self.minimum_purchase_amount < 0:

            raise ValidationError(
                {
                    "minimum_purchase_amount": "Minimum purchase amount cannot be negative."
                }
            )

        if self.maximum_discount_amount < 0:

            raise ValidationError(
                {
                    "maximum_discount_amount": "Maximum discount amount cannot be negative."
                }
            )

        if self.offer_type == "PRODUCT":

            existing_offer = Offer.objects.filter(
                product=self.product,
                is_active=True,
                is_deleted=False,
                end_date__gte=timezone.now(),
            ).exclude(pk=self.pk)

            if existing_offer.exists():

                raise ValidationError(
                    {"product": "An active offer already exists for this product."}
                )

        if self.offer_type == "CATEGORY":
            existing_offer = Offer.objects.filter(
                category=self.category,
                is_active=True,
                is_deleted=False,
                end_date__gte=timezone.now(),
            ).exclude(pk=self.pk)
            if existing_offer.exists():

                raise ValidationError(
                    {"category": "An active offer already exists for this category."}
                )

    class Meta:

        indexes = [
            models.Index(fields=["offer_type"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["start_date"]),
            models.Index(fields=["end_date"]),
        ]

        ordering = ["-created_at"]

    def __str__(self):

        return self.offer_name

    def save(self, *args, **kwargs):

        self.offer_name = self.offer_name.strip()

        self.full_clean()

        super().save(*args, **kwargs)
