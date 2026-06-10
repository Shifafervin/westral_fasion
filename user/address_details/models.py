from django.db import models
from django.conf import settings
import re
from django.core.exceptions import ValidationError


class Address(models.Model):
    ADDRESS_TYPE = (
        ("home", "Home"),
        ("work", "Work"),
        ("other", "Other"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    pincode = models.CharField(max_length=6)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    address_line = models.TextField()
    country = models.CharField(max_length=15, null=True)

    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):

        self.full_name = self.full_name.strip()

        if len(self.full_name) < 3:

            raise ValidationError(
                {"full_name": "Full name must contain at least 3 characters."}
            )

        if len(self.full_name) > 100:

            raise ValidationError({"full_name": "Full name is too long."})

        if not re.match(r"^[A-Za-z ]+$", self.full_name):

            raise ValidationError(
                {"full_name": "Full name can contain only letters and spaces."}
            )

        if not re.match(r"^[6-9]\d{9}$", self.phone):

            raise ValidationError({"phone": "Enter a valid 10 digit mobile number."})

        if not re.match(r"^[1-9][0-9]{5}$", self.pincode):

            raise ValidationError({"pincode": "Enter a valid pincode."})

        if len(self.city.strip()) < 2:

            raise ValidationError({"city": "City name is too short."})

        if not re.match(r"^[A-Za-z ]+$", self.city):

            raise ValidationError({"city": "City can contain only letters."})

        if len(self.state.strip()) < 2:

            raise ValidationError({"state": "State name is too short."})

        if not re.match(r"^[A-Za-z ]+$", self.state):

            raise ValidationError({"state": "State can contain only letters."})

        if len(self.address_line.strip()) < 15:

            raise ValidationError(
                {"address_line": "Address must contain at least 15 characters."}
            )

        if len(self.address_line.strip()) > 250:

            raise ValidationError({"address_line": "Address is too long."})

        allowed_types = ["home", "work", "other"]

        if self.address_type not in allowed_types:

            raise ValidationError({"address_type": "Invalid address type."})

    def save(self, *args, **kwargs):

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.city}"
