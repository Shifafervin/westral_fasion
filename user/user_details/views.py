from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Profile
import re
from django.core.mail import send_mail
from django.views.decorators.cache import never_cache, cache_control
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
import random, time
from .models import PasswordResetOTP
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from user.decorators import user_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()


def validate_password_strength(password):

    if len(password) < 8:
        return "Password must be at least 8 characters."

    if not re.search(r"[A-Z]", password):
        return "Add at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return "Add at least one lowercase letter."

    if not re.search(r"\d", password):
        return "Add at least one number."

    if not re.search(r"[!@#$%^&*]", password):
        return "Add at least one special character (!@#$%^&*)."

    return None


@never_cache
@login_required(login_url="login")
def profile_page(request):
    user = request.user

    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":

        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()

        if not email:
            messages.error(request, "Email is required")
            return redirect("user_details:profile")

        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email already exists")
            return redirect("user_details:profile")

        if full_name:
            parts = full_name.split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""

        user.email = email
        user.save()

        profile.phone = phone
        profile.save()

        messages.success(request, "Profile updated successfully")
        return redirect("user_details:profile")

    return render(
        request,
        "profile.html",
        {
            "user": user,
            "profile": profile,
        },
    )


@user_required
def edit_profile(request):

    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == "POST":

        full_name = request.POST.get("full_name", "").strip()
        full_name = " ".join(full_name.split())
        if not full_name:
            messages.error(request, "Full name is required.")
            return render(request, "edit_profile.html")

        if len(full_name) < 3:
            messages.error(request, "Name must be at least 3 characters.")
            return render(request, "edit_profile.html")

        if len(full_name) > 50:
            messages.error(request, "Name cannot exceed 50 characters.")
            return render(request, "edit_profile.html")

        if not re.match(r"^[A-Za-z\s\.\'-]+$", full_name):
    
                messages.error(
                    request,
                    "Name can contain letters, spaces, dots, hyphens and apostrophes only."
                )
                return render(request, "edit_profile.html")

        new_email = request.POST.get("email", "").strip().lower()
        if not new_email:
            messages.error(request, "Email is required.")
            return render(request, "edit_profile.html")

        try:
            validate_email(new_email)

        except ValidationError:
            messages.error(
                request,
                "Enter a valid email address."
            )
            return render(request, "edit_profile.html")
        if User.objects.filter(
            email=new_email
        ).exclude(
            id=request.user.id
        ).exists():

            messages.error(
                request,
                "Email already exists."
            )

            return render(
                request,
                "edit_profile.html"
            )
        phone = request.POST.get("phone", "").strip()
        image = request.FILES.get("profile_image")

    
    

        if not phone:

            messages.error(
                request,
                "Phone number is required."
            )

            return render(
                request,
                "edit_profile.html"
            )

        if not re.fullmatch(
            r"\d{10}",
            phone
        ):

            messages.error(
                request,
                "Phone number must contain exactly 10 digits."
            )

            return render(
                request,
                "edit_profile.html"
            )

        if phone[0] not in ["6", "7", "8", "9"]:

            messages.error(
                request,
                "Enter a valid Indian mobile number."
            )

            return render(
                request,
                "edit_profile.html"
            )

        invalid_numbers = [
            "0000000000",
            "1111111111",
            "2222222222",
            "3333333333",
            "4444444444",
            "5555555555",
            "6666666666",
            "7777777777",
            "8888888888",
            "9999999999",
            "1234567890",
        ]

        if phone in invalid_numbers:

            messages.error(
                request,
                "Enter a valid phone number."
            )

            return render(
                request,
                "edit_profile.html"
            )
        
        if image:

            allowed_extensions = ["jpg", "jpeg", "png", "webp"]

            extension = image.name.split(".")[-1].lower()

            if extension not in allowed_extensions:

                messages.error(
                    request,
                    "Only JPG, JPEG, PNG and WEBP images are allowed."
                )

                return render(request, "edit_profile.html")

            if image.size > 2 * 1024 * 1024:

                messages.error(
                    request,
                    "Image size must be less than 2MB."
                )

                return render(request, "edit_profile.html")

            if profile.image and profile.image.name != "default.png":
                profile.image.delete(save=False)

            profile.image = image
            profile.save()

        profile.phone = phone
        profile.save()


        if full_name:
            parts = full_name.split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""


        if new_email and new_email != user.email:
            otp = str(random.randint(100000, 999999))
            request.session["otp"] = otp
            request.session["pending_email"] = new_email
            request.session["otp_time"] = str(timezone.now())

            send_mail(
                "Verify your new email",
                f"Your OTP is {otp}",
                "your_email@gmail.com",
                [new_email],
                fail_silently=False,
            )

            user.save()
            return redirect("user_details:verify_email_otp")
        
        user.save()

        messages.success(request, "Profile updated successfully")
        return redirect("user_details:profile")

    return render(request, "edit_profile.html")


@user_required
def verify_email_otp(request):

    if request.method == "POST":

        otp_digits = [request.POST.get(f"otp{i}", "") for i in range(1, 7)]

        if not all(d.isdigit() and len(d) == 1 for d in otp_digits):
            return render(
                request, "verify_otp.html", {"error": "Enter complete 6-digit OTP"}
            )

        entered_otp = "".join(otp_digits)

        session_otp = request.session.get("otp")
        new_email = request.session.get("pending_email")
        otp_time = request.session.get("otp_time")

        if not session_otp or not new_email:
            messages.error(request, "Session expired. Try again.")
            return redirect("user_details:edit_profile")

        if otp_time:
            otp_time = timezone.datetime.fromisoformat(otp_time)
            if timezone.now() > otp_time + timedelta(minutes=1):
                return render(
                    request, "verify_otp.html", {"error": "OTP expired. Resend again."}
                )

        if entered_otp != session_otp:
            return render(request, "profile_emailverify.html", {"error": "Invalid OTP"})

        user = request.user
        user.email = new_email
        user.save()

        request.session.pop("otp", None)
        request.session.pop("pending_email", None)
        request.session.pop("otp_time", None)

        messages.success(request, "Email updated successfully")

        return redirect("user_details:profile")

    return render(request, "profile_emailverify.html")


@user_required
def resend_email_otp(request):

    new_email = request.session.get("pending_email")

    if not new_email:
        messages.error(request, "Session expired. Try again.")
        return redirect("user_details:edit_profile")

    otp = str(random.randint(100000, 999999))

    request.session["otp"] = otp
    request.session["otp_time"] = str(timezone.now())

    send_mail(
        "Resend OTP - Verify your email",
        f"Your new OTP is {otp}",
        "your_email@gmail.com",
        [new_email],
        fail_silently=False,
    )

    messages.success(request, "OTP resent successfully")

    return redirect("user_details:verify_email_otp")


def change_password(request):

    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password", "")
        if new_password.strip() != new_password:

            messages.error(
                request,
                "Password cannot start or end with spaces.",
                extra_tags="password"
            )

            return render(
                request,
                "change_password.html"
            )
        confirm_password = request.POST.get("confirm_password")

        user = request.user

        if not user.check_password(current_password):
            messages.error(
                request, "Current password is incorrect.", extra_tags="password"
            )

            return render(request, "change_password.html")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.", extra_tags="password")

            return render(request, "change_password.html")

        if len(new_password) < 8:

            messages.error(
                request,
                "Password must be at least 8 characters long.",
                extra_tags="password"
            )

            return render(
                request,
                "change_password.html"
            )

        if len(new_password) > 128:

            messages.error(
                request,
                "Password is too long.",
                extra_tags="password"
            )

            return render(
                request,
                "change_password.html"
            )
        if not re.search(r"[A-Z]", new_password):
            messages.error(
                request,
                "Password must contain at least one uppercase letter.",
                extra_tags="password"
            )
            return render(request, "change_password.html")

        if not re.search(r"[0-9]", new_password):
            messages.error(
                request,
                "Password must contain at least one number.",
                extra_tags="password"
            )
            return render(request, "change_password.html")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
            messages.error(
                request,
                "Password must contain at least one special character.",
                extra_tags="password"
            )

            return render(
                request,
                "change_password.html"
            )

        if not re.search(r"[a-z]", new_password):

            messages.error(
                request,
                "Password must contain at least one lowercase letter.",
                extra_tags="password"
            )

            return render(
                request,
                "change_password.html"
            )  
        if user.check_password(new_password):

            messages.error(
                request,
                "New password cannot be the same as your current password.",
                extra_tags="password"
            )

            return render(
                request,
                "change_password.html"
            )
                

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)

        messages.success(
            request, "Password changed successfully.", extra_tags="password"
        )

        return redirect("user_details:profile")

    return render(request, "change_password.html")


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_confirm(request):
    return render(request, "logout_confirmation.html")


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_view(request):
    logout(request)
    return redirect("login")


def profile_forgotpassword(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email not found")
            return render(request, "profileforgot_password.html")

        PasswordResetOTP.objects.filter(user=user, is_used=False).delete()

        otp = str(random.randint(100000, 999999))

        PasswordResetOTP.objects.create(user=user, otp=otp)

        request.session["reset_email"] = email

        send_mail(
            "Password Reset OTP",
            f"Your OTP is {otp}. It expires in 1 minute.",
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )

        return redirect("user_details:profileverify_otp")

    return render(request, "profileforgot_password.html")


def profile_verify_otp(request):
    error = None
    email = request.session.get("reset_email")

    if not email:
        return redirect("profile_forgotpassword")

    user = User.objects.get(email=email)

    if request.method == "POST":
        entered_otp = "".join([request.POST.get(f"otp{i}", "") for i in range(1, 7)])

        otp_obj = PasswordResetOTP.objects.filter(
            user=user, otp=entered_otp, is_used=False
        ).last()

        if not otp_obj:
            error = "Invalid OTP"

        elif otp_obj.is_expired():
            error = "OTP expired. Please resend."

        else:
            otp_obj.is_used = True
            otp_obj.save()

            request.session["otp_verified"] = True
            return redirect("user_details:profilereset_password")

    return render(request, "profile_verifyemail.html", {"error": error})


def profile_resend_otp(request):
    email = request.session.get("reset_email")

    if not email:
        return redirect("profile_forgotpassword")

    user = User.objects.get(email=email)

    PasswordResetOTP.objects.filter(user=user, is_used=False).delete()

    otp = str(random.randint(100000, 999999))

    PasswordResetOTP.objects.create(user=user, otp=otp)

    send_mail(
        "New OTP",
        f"Your new OTP is {otp}. It expires in 1 minute.",
        settings.DEFAULT_FROM_EMAIL,
        [email],
    )

    messages.success(request, "New OTP sent")
    return redirect("profileverify_otp")


def profile_resetpassword(request):
    email = request.session.get("reset_email")
    verified = request.session.get("otp_verified")

    if not email or not verified:
        return redirect("user_details:profile_forgotpassword")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")

        if password != confirm:
            messages.error(request, "Passwords do not match")
            return render(request, "profile_resetpassword.html")

        error = validate_password_strength(password)
        if error:
            messages.error(request, error)
            return render(request, "profile_resetpassword.html")

        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        request.session.flush()

        messages.success(request, "Password reset successful")
        return redirect("login")

    return render(request, "profile_resetpassword.html")
