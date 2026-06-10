from django import forms

from .models import Category


class CategoryForm(forms.ModelForm):

    class Meta:

        model = Category

        fields = [
            "category_name",
            "category_description",
            "category_image",
            "is_active",
        ]

        widgets = {
            "category_name": forms.TextInput(
                attrs={"placeholder": "Enter category name"}
            ),
            "category_description": forms.Textarea(
                attrs={"placeholder": "Enter category description"}
            ),
        }

    def clean_category_name(self):

        category_name = self.cleaned_data["category_name"].strip()

        return category_name
