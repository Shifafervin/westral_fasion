from django.db import models
from django.conf import settings

class Address(models.Model):
    ADDRESS_TYPE = (
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    pincode = models.CharField(max_length=6)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    address_line = models.TextField()
    country= models.CharField(max_length=15,null=True)

    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPE)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.city}"