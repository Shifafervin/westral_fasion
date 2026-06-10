from django.db import models

from django.core.exceptions import ValidationError

from django.utils.text import slugify

from admin.admin_category.models import Category

import re
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

# ================= PRODUCT MODEL =================


class Product(models.Model):

    product_name = models.CharField(max_length=200)

    slug = models.SlugField(blank=True, null=True)

    description = models.TextField()

    fit_type = models.CharField(max_length=100, null=True, blank=True)

    materials = models.TextField(null=True, blank=True)

    care_guide = models.TextField(null=True, blank=True)

    return_policy = models.TextField(null=True, blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )

    is_deleted = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = ["-id"]

        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_deleted"]),
            models.Index(fields=["slug"]),
        ]

    def clean(self):

        self.product_name = self.product_name.strip()

        if not self.product_name:

            raise ValidationError({"product_name": "Product name is required."})

        if len(self.product_name) < 3:

            raise ValidationError(
                {"product_name": "Product name must be at least 3 characters long."}
            )

        if len(self.product_name) > 200:

            raise ValidationError(
                {"product_name": "Product name cannot exceed 200 characters."}
            )

        if "_" in self.product_name:

            raise ValidationError(
                {"product_name": "Underscore (_) is not allowed in product names."}
            )

        if self.product_name.isdigit():

            raise ValidationError(
                {"product_name": "Product name cannot contain only numbers."}
            )

        if not re.search(r"[A-Za-z]", self.product_name):

            raise ValidationError(
                {"product_name": "Product name must contain at least one letter."}
            )

        if not re.match(r"^[A-Za-z0-9\s\-&()]+$", self.product_name):

            raise ValidationError(
                {
                    "product_name": "Only letters, numbers, spaces, hyphens (-), &, and parentheses are allowed."
                }
            )

        cleaned_name = self.product_name.replace(" ", "")

        if len(set(cleaned_name)) == 1:

            raise ValidationError({"product_name": "Invalid product name."})

        existing_product = Product.objects.filter(
            product_name__iexact=self.product_name, is_deleted=False
        ).exclude(id=self.id)

        if existing_product.exists():

            raise ValidationError(
                {"product_name": "A product with this name already exists."}
            )

        if not self.description:

            raise ValidationError({"description": "Description is required."})

        description = self.description.strip()

        if len(description) < 20:

            raise ValidationError(
                {"description": "Description must contain at least 20 characters."}
            )

        if len(description.split()) < 5:

            raise ValidationError(
                {"description": "Description must contain at least 5 words."}
            )

        if not self.category_id:

            raise ValidationError({"category": "Please select a category."})

        if self.fit_type:

            self.fit_type = self.fit_type.strip()

            if len(self.fit_type) < 2:

                raise ValidationError({"fit_type": "Fit type is too short."})

        if self.materials:

            self.materials = self.materials.strip()

            if len(self.materials) < 3:

                raise ValidationError(
                    {"materials": "Material information is too short."}
                )

        if self.care_guide:

            self.care_guide = self.care_guide.strip()

            if len(self.care_guide) < 5:

                raise ValidationError({"care_guide": "Care guide is too short."})

        if self.return_policy:

            self.return_policy = self.return_policy.strip()

            if len(self.return_policy) < 5:

                raise ValidationError({"return_policy": "Return policy is too short."})

    def save(self, *args, **kwargs):

        if not self.slug:

            base_slug = slugify(self.product_name)

            slug = base_slug

            counter = 1

            while Product.objects.filter(slug=slug).exclude(id=self.id).exists():

                slug = f"{base_slug}-{counter}"

                counter += 1

            self.slug = slug

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.product_name


# ================= VARIANT MODEL =================


class Variant(models.Model):

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants"
    )

    size = models.CharField(max_length=20)

    sku = models.CharField(max_length=100, unique=True)

    color = models.CharField(max_length=100)

    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(1)]
    )

    weight = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    stock = models.PositiveIntegerField(default=0)

    low_stock_threshold = models.PositiveIntegerField(default=5)

    is_active = models.BooleanField(default=True)

    is_default = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

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

        return self.stock <= self.low_stock_threshold

    def clean(self):

        if self.stock < 0:

            raise ValidationError({"stock": "Stock cannot be negative"})

        if self.product_id and self.is_default:

            default_variant = Variant.objects.filter(
                product=self.product, is_default=True, is_deleted=False
            ).exclude(id=self.id)

            if default_variant.exists():

                raise ValidationError(
                    {"is_default": "Only one default variant is allowed"}
                )

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):

        return f"{self.product.product_name}" f" - {self.size}"


# ================= PRODUCT IMAGE MODEL =================


class ProductImage(models.Model):

    variant = models.ForeignKey(
        Variant, on_delete=models.CASCADE, related_name="images"
    )

    image = models.ImageField(upload_to="variants/")

    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ["id"]

    def clean(self):

        allowed_sizes = ["S", "M", "L", "XL"]

        if not self.size:

            raise ValidationError({"size": "Size is required."})

        if self.size not in allowed_sizes:

            raise ValidationError({"size": "Invalid size selected."})

        if not self.color:

            raise ValidationError({"color": "Color is required."})

        self.color = self.color.strip()

        if len(self.color) < 3:

            raise ValidationError(
                {"color": "Color must contain at least 3 characters."}
            )

        if "_" in self.color:

            raise ValidationError({"color": "Underscores are not allowed."})

        if self.color.isdigit():

            raise ValidationError({"color": "Color cannot contain only numbers."})

        if not re.match(r"^[A-Za-z\s]+$", self.color):

            raise ValidationError({"color": "Color can contain only letters."})

        if not self.sku:

            raise ValidationError({"sku": "SKU is required."})

        self.sku = self.sku.strip().upper()

        if len(self.sku) < 5:

            raise ValidationError({"sku": "SKU must contain at least 5 characters."})

        if "_" in self.sku:

            raise ValidationError({"sku": "Underscores are not allowed in SKU."})

        if not re.match(r"^[A-Z0-9\-]+$", self.sku):

            raise ValidationError(
                {"sku": "SKU can contain only letters, numbers and hyphens."}
            )

        duplicate_sku = Variant.objects.filter(sku__iexact=self.sku).exclude(id=self.id)

        if duplicate_sku.exists():

            raise ValidationError({"sku": "SKU already exists."})

        if self.price is None:

            raise ValidationError({"price": "Price is required."})

        if self.price <= 0:

            raise ValidationError({"price": "Price must be greater than 0."})

        if self.price < 10:

            raise ValidationError({"price": "Price must be at least ₹10."})

        if self.price > 100000:

            raise ValidationError({"price": "Price exceeds maximum limit."})

        if self.weight <= 0:

            raise ValidationError({"weight": "Weight must be greater than 0."})

        if self.weight < 10:

            raise ValidationError({"weight": "Weight must be at least 10 grams."})

        if self.weight > 50000:

            raise ValidationError({"weight": "Weight exceeds maximum limit."})

        if self.stock < 0:

            raise ValidationError({"stock": "Stock cannot be negative."})

        if self.stock > 100000:

            raise ValidationError({"stock": "Stock exceeds maximum limit."})

        if self.product_id and self.is_default:

            default_variant = Variant.objects.filter(
                product=self.product, is_default=True, is_deleted=False
            ).exclude(id=self.id)

            if default_variant.exists():

                raise ValidationError(
                    {"is_default": "Only one default variant is allowed."}
                )

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.variant.sku
