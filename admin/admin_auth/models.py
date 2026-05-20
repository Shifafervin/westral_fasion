from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    
    # 🔥 make email unique (important)
    email = models.EmailField(unique=True)

    # 🔥 block system
    is_blocked = models.BooleanField(default=False)

    # 🔥 optional profile image
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    # 🔥 use email as login (optional but recommended)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email