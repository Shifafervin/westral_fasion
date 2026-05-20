from django.conf import settings
from django.db import models
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)

    # 🔥 ADD THIS
    image = models.ImageField(upload_to='profile_images/', default='default.png')

    def __str__(self):
        return self.user.username
    
User = get_user_model()

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=1)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"