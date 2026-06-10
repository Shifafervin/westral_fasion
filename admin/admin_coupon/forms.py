from django import forms
from django.utils import timezone
from .models import Coupon


class CouponForm(forms.ModelForm):

    class Meta:
        model = Coupon

        exclude = [
            "used_count",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

        widgets = {
            "code": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "Eg. SUMMER2026"}
            ),
            "discount_type": forms.RadioSelect(),
            "discount_value": forms.NumberInput(
                attrs={"class": "form-input", "min": "1"}
            ),
            "minimum_purchase_amount": forms.NumberInput(
                attrs={"class": "form-input", "min": "0"}
            ),
            "maximum_discount_amount": forms.NumberInput(
                attrs={"class": "form-input", "min": "0"}
            ),
            "total_usage_limit": forms.NumberInput(
                attrs={"class": "form-input", "min": "1"}
            ),
            "usage_limit_per_user": forms.NumberInput(
                attrs={"class": "form-input", "min": "1"}
            ),
            "valid_from": forms.DateInput(attrs={"class": "form-date", "type": "date"}),
            "valid_to": forms.DateInput(attrs={"class": "form-date", "type": "date"}),
            "is_active": forms.CheckboxInput(),
        }

    def clean_code(self):

        code = self.cleaned_data["code"].strip().upper()

        if Coupon.objects.filter(code=code).exclude(pk=self.instance.pk).exists():

            raise forms.ValidationError("Coupon code already exists.")

        return code

    def clean(self):

        cleaned_data = super().clean()

        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")

        total_limit = cleaned_data.get("total_usage_limit")

        user_limit = cleaned_data.get("usage_limit_per_user")

        if valid_from and valid_to:

            if valid_from >= valid_to:

                raise forms.ValidationError("End date must be after start date.")

        if total_limit and user_limit:

            if user_limit > total_limit:

                raise forms.ValidationError(
                    "User limit cannot exceed total usage limit."
                )

        return cleaned_data

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["discount_type"].choices = [
            ("Percentage", "Percentage"),
            ("Fixed", "Fixed"),
        ]
