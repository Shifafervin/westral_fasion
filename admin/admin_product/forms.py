from django import forms
from .models import Product
from .models import Variant

class ProductForm(forms.ModelForm):

    class Meta:

        model = Product

        fields = [

            "product_name",

            "description",

            "fit_type",

            "materials",

            "care_guide",

            "return_policy",

            "category",

            "is_active",

        ]

        widgets = {

            "description":
            forms.Textarea(

                attrs={
                    "rows": 4
                }

            ),

            "materials":
            forms.Textarea(

                attrs={
                    "rows": 4
                }

            ),

            "care_guide":
            forms.Textarea(

                attrs={
                    "rows": 4
                }

            ),

            "return_policy":
            forms.Textarea(

                attrs={
                    "rows": 4
                }

            ),

        }

    def clean_product_name(self):

        product_name = self.cleaned_data[
            "product_name"
        ].strip()

        return product_name

class VariantForm(forms.ModelForm):

    class Meta:

        model = Variant

        fields = [

            "color",

            "size",

            "sku",

            "price",

            "stock",

            "weight",

            "is_active",

            "is_default",

        ]

    def clean_sku(self):

        sku = self.cleaned_data[
            "sku"
        ].strip().upper()

        return sku

    def clean_price(self):

        price = self.cleaned_data[
            "price"
        ]

        if price <= 0:

            raise forms.ValidationError(

                "Invalid price amount"

            )

        return price

    def clean_stock(self):

        stock = self.cleaned_data[
            "stock"
        ]

        if stock < 0:

            raise forms.ValidationError(

                "Invalid stock quantity"

            )

        return stock

    def clean_weight(self):

        weight = self.cleaned_data[
            "weight"
        ]

        if weight <= 0:

            raise forms.ValidationError(

                "Invalid weight"

            )

        return weight