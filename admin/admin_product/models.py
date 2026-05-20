from django.db import models

from django.core.exceptions import ValidationError

from django.utils.text import slugify

from admin.admin_category.models import Category


# ================= PRODUCT MODEL =================

class Product(models.Model):

    product_name = models.CharField(
        max_length=200
    )

    slug = models.SlugField(
        blank=True,
        null=True
    )

    description = models.TextField()

    fit_type = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    materials = models.TextField(
        null=True,
        blank=True
    )

    care_guide = models.TextField(
        null=True,
        blank=True
    )

    return_policy = models.TextField(
        null=True,
        blank=True
    )

    category = models.ForeignKey(

        Category,

        on_delete=models.CASCADE,

        related_name="products"
    )

    is_deleted = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ["-id"]

        indexes = [

            models.Index(fields=["is_active"]),

            models.Index(fields=["is_deleted"]),

            models.Index(fields=["slug"]),

        ]

    def clean(self):

        self.product_name = (
            self.product_name.strip()
        )

        if not self.product_name:

            raise ValidationError({

                "product_name":
                "Product name is required"

            })

        existing_product = Product.objects.filter(

            product_name__iexact=self.product_name,

            is_deleted=False

        ).exclude(id=self.id)

        if existing_product.exists():

            raise ValidationError({

                "product_name":
                "Product already exists"

            })

    def save(self, *args, **kwargs):

        if not self.slug:

            base_slug = slugify(
                self.product_name
            )

            slug = base_slug

            counter = 1

            while Product.objects.filter(
                slug=slug
            ).exclude(id=self.id).exists():

                slug = (
                    f"{base_slug}-{counter}"
                )

                counter += 1

            self.slug = slug

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.product_name


# ================= VARIANT MODEL =================

class Variant(models.Model):

    product = models.ForeignKey(

        Product,

        on_delete=models.CASCADE,

        related_name="variants"
    )

    size = models.CharField(
        max_length=20
    )

    sku = models.CharField(
        max_length=100,
        unique=True
    )

    color = models.CharField(
        max_length=100
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    weight = models.PositiveIntegerField()

    stock = models.PositiveIntegerField(
        default=0
    )

    low_stock_threshold = models.PositiveIntegerField(
        default=5
    )

    is_active = models.BooleanField(
        default=True
    )

    is_default = models.BooleanField(
        default=False
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

    class Meta:

        ordering = ["-id"]

        indexes = [

            models.Index(fields=["sku"]),

            models.Index(fields=["is_active"]),

            models.Index(fields=["is_deleted"]),

        ]

    @property
    def final_price(self):

        return self.price

    @property
    def is_low_stock(self):

        return (
            self.stock <=
            self.low_stock_threshold
        )

    def clean(self):

        if self.stock < 0:

            raise ValidationError({

                "stock":
                "Stock cannot be negative"

            })

        if self.product_id and self.is_default:

            default_variant = Variant.objects.filter(

                product=self.product,

                is_default=True,

                is_deleted=False

            ).exclude(id=self.id)

            if default_variant.exists():

                raise ValidationError({

                    "is_default":
                    "Only one default variant is allowed"

                })

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):

        return (
            f"{self.product.product_name}"
            f" - {self.size}"
        )


# ================= PRODUCT IMAGE MODEL =================

class ProductImage(models.Model):

    variant = models.ForeignKey(

        Variant,

        on_delete=models.CASCADE,

        related_name="images"
    )

    image = models.ImageField(
        upload_to="variants/"
    )

    is_primary = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ["id"]

    def clean(self):

        primary_image = ProductImage.objects.filter(

            variant=self.variant,

            is_primary=True

        ).exclude(id=self.id)

        if self.is_primary and primary_image.exists():

            raise ValidationError({

                "is_primary":
                "Only one primary image is allowed"

            })

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.variant.sku
    