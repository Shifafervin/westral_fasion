from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils import timezone
import re

class Coupon(models.Model):

    PERCENTAGE = "Percentage"

    FIXED = "Fixed"

    DISCOUNT_TYPES = [

        (PERCENTAGE, "Percentage"),

        (FIXED, "Fixed")

    ]

    code = models.CharField(

        max_length=50,
        unique=True

    )

    description = models.TextField(

    blank=True,
    null=True

    )

    discount_type = models.CharField(

        max_length=20,
        choices=DISCOUNT_TYPES

    )

    discount_value = models.DecimalField(

    max_digits=10,
    decimal_places=2,
    validators=[MinValueValidator(0)]

    )

    minimum_purchase_amount = models.DecimalField(

    max_digits=10,
    decimal_places=2,
    default=0,
    validators=[MinValueValidator(0)]

   )

    maximum_discount_amount = models.DecimalField(

    max_digits=10,
    decimal_places=2,
    null=True,
    blank=True,
    validators=[MinValueValidator(0)]

    )

    total_usage_limit = models.PositiveIntegerField(

    default=1,
    validators=[MinValueValidator(1)]

    )

    usage_limit_per_user = models.PositiveIntegerField(

    default=1,
    validators=[MinValueValidator(1)]

    )

    used_count = models.PositiveIntegerField(

        default=0

    )

    valid_from = models.DateField()

    valid_to = models.DateField()

    is_active = models.BooleanField(

        default=True

    )

    is_deleted = models.BooleanField(

        default=False

    )

    created_at = models.DateTimeField(

        auto_now_add=True

    )

    updated_at = models.DateTimeField(

        auto_now=True

    )
    
    def clean(self):

        self.code = self.code.strip().upper()

        if not re.match(
            r'^(?=.*[A-Z])[A-Z0-9]+$',
            self.code.upper()
        ):
            raise ValidationError({
                "code":
                "Coupon code must contain only uppercase letters and numbers. No spaces, underscores or special characters are allowed."
            })

        if self.valid_to <= self.valid_from:

            raise ValidationError({
                "valid_to":
                "End date must be after start date."
            })

        if self.discount_type == self.PERCENTAGE:

            if self.discount_value <= 0:

                raise ValidationError({
                    "discount_value":
                    "Percentage discount must be greater than 0."
                })

            if self.discount_value > 50:

                raise ValidationError({
                    "discount_value":
                    "Percentage discount cannot exceed 50%."
                })    


        if self.discount_type == self.FIXED:

            if self.discount_value <= 0:

                raise ValidationError({
                    "discount_value":
                    "Flat discount must be greater than 0."
                })

            if self.discount_value > 300:

                raise ValidationError({
                    "discount_value":
                    "Flat discount cannot exceed ₹300."
                })

        if self.maximum_discount_amount <= 0:

            raise ValidationError({
                "maximum_discount_amount":
                "Maximum discount must be greater than zero."
            })

        if self.total_usage_limit <= 0:

            raise ValidationError({
                "total_usage_limit":
                "Usage limit must be greater than zero."
            })

        if self.usage_limit_per_user <= 0:

            raise ValidationError({
                "usage_limit_per_user":
                "User usage limit must be greater than zero."
            })

        if self.valid_from >= self.valid_to:

            raise ValidationError(
                "Invalid coupon date range."
        )
    def save(
        self,
        *args,
        validate=True,
        **kwargs
    ):

        self.code = self.code.upper().strip()

        if validate:
            self.full_clean()

        super().save(
            *args,
            **kwargs
        )

    def __str__(self):

        return self.code    