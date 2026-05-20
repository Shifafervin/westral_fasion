from django.db import models
from django.contrib.auth.models import  BaseUserManager
from django.contrib.auth.models import AbstractUser



class UserManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email required")

        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, full_name, password=None):
        user = self.create_user(email, full_name, password)
        user.is_staff = True
        user.is_superuser = True
        user.is_verified = True
        user.save()
        return user




class User(AbstractUser):

    email = models.EmailField(unique=True)

    # 🔥 FIX CLASH HERE
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',
        blank=True
    )


class OTP(models.Model):
    PURPOSE_CHOICES = (
        ('signup', 'Signup'),
        ('reset_password', 'Reset Password'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)