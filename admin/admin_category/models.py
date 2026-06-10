from django.db import models

from django.core.exceptions import ValidationError


class Category(models.Model):

    category_name = models.CharField(max_length=100, unique=True)

    category_description = models.TextField(null=True, blank=True)

    category_image = models.ImageField(upload_to="categories/")

    is_active = models.BooleanField(default=True)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = ["-id"]

        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_deleted"]),
        ]

    def clean(self):

        self.category_name = self.category_name.strip()

        if not self.category_name:

            raise ValidationError({"category_name": "Category name is required"})

        existing_category = Category.objects.filter(
            category_name__iexact=self.category_name, is_deleted=False
        ).exclude(id=self.id)

        if existing_category.exists():

            raise ValidationError({"category_name": "Category already exists"})

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):

        return self.category_name
