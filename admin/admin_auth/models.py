from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class CustomUser(AbstractUser):

    email = models.EmailField(unique=True)

    is_blocked = models.BooleanField(default=False)

    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    referred_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals",
    )
    show_referral_popup = models.BooleanField(default=False)

    referral_reward_given = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        if not self.referral_code:

            self.referral_code = str(uuid.uuid4())[:8].upper()

        super().save(*args, **kwargs)

    # 🔥 optional profile image
    profile_image = models.ImageField(upload_to="profiles/", blank=True, null=True)

    # 🔥 use email as login (optional but recommended)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
