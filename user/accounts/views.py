import re
import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
import time
from admin.admin_product.models import Product
from admin.admin_category.models import Category
from user.decorators import user_required
from admin.admin_orders.models import Wallet, WalletTransaction
from decimal import Decimal
from user.user_products.models import Variant
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone

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
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    ref_code = request.GET.get("ref")

    if ref_code:

        request.session["referral_code"] = ref_code.upper()

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        referral_code = request.POST.get("referral_code", "").strip().upper()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm_password", "")
        terms = request.POST.get("terms", "")

        errors = {}

        if not name:

            errors["name"] = "Full name is required"

        elif len(name) < 3:

            errors["name"] = "Name must be at least 3 characters"

        elif not re.match(r"^[A-Za-z\s\.\'-]+$", name):

            errors["name"] = "Name must contain only letters"

        elif name.strip().count(" ") < 1:

            errors["name"] = "Enter first and last name"

        if not email:
            errors["email"] = "Email is required"

        else:
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = "Enter a valid email address"    

        if not password:
            errors["password"] = "Password is required"

        if password != confirm:
            errors["confirm_password"] = "Passwords do not match"

        if not terms:
            errors["terms"] = "You must accept the Terms of Service and Privacy Policy"    

        password_error = validate_password_strength(password)
        if password_error:
            errors["password"] = password_error

        if User.objects.filter(email=email).exists():
            errors["email"] = "Email already exists"

        if referral_code:
            if not User.objects.filter(
                referral_code=referral_code
            ).exists():
                errors["referral_code"] = "Invalid referral code"

        if errors:

            response = render(
                request,
                "signup.html",
                {
                    "errors": errors,
                    "name": name,
                    "email": email,
                    "referral_code": referral_code,
                },
            )

            response.status_code = 400

            return response

        last_sent = request.session.get("otp_sent_time")

        if last_sent:

            elapsed = time.time() - last_sent

            if elapsed < 60:

                errors["email"] = (
                    f"Please wait {int(60 - elapsed)} seconds before requesting another OTP."
                )

                return render(
                    request,
                    "signup.html",
                    {
                        "errors": errors,
                        "name": name,
                        "email": email,
                        "referral_code": referral_code,
                    },
                )

        otp = str(random.randint(100000, 999999))

        otp_expiry = timezone.now() + timedelta(minutes=1)

        request.session["signup_data"] = {
            "name": name,
            "email": email,
            "password": password,
            "otp": otp,
            "referral_code": referral_code,
            "otp_expiry": otp_expiry.isoformat(),
            "otp_created": timezone.now().isoformat(),
        }

        request.session["otp_message"] = f"A new OTP has been sent to {email}"

        send_mail(
            "Your OTP Code",
            f"Your OTP is {otp}",
            "your_email@gmail.com",
            [email],
            fail_silently=False,
        )
        request.session["otp_sent_time"] = time.time()

        return redirect("signup_verify")

    return render(request, "signup.html")

@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_verify(request):

    if request.method == "POST":

        user_otp = "".join([request.POST.get(f"otp{i}", "") for i in range(1, 7)])

        if len(user_otp) != 6:

            messages.error(
                request,
                "Enter complete OTP"
            )

            data = request.session.get("signup_data")

            remaining_seconds = 0

            if data and data.get("otp_expiry"):

                expiry_time = timezone.datetime.fromisoformat(
                    data["otp_expiry"]
                )

                remaining_seconds = max(
                    0,
                    int((expiry_time - timezone.now()).total_seconds())
                )

            response = render(
                request,
                "signup_verify.html",
                {
                    "remaining_seconds": remaining_seconds,
                    "otp_expiry": data.get("otp_expiry"),
                }
            )

            response.status_code = 400

            return response

        data = request.session.get("signup_data")

        if not data:
            messages.error(request, "Session expired. Signup again.")
            return redirect("signup")
        
        expiry = data.get("otp_expiry")

        if not expiry:
            messages.error(request, "OTP expired. Please signup again.")
            return redirect("signup")

        expiry_time = timezone.datetime.fromisoformat(expiry)

        if timezone.now() > expiry_time:

            messages.error(
                request,
                "OTP expired. Please click Resend OTP."
            )

            remaining_seconds = 0

            response = render(
                request,
                "signup_verify.html",
                {
                    "remaining_seconds": remaining_seconds,
                    "otp_expiry": data.get("otp_expiry"),
                }
            )

            response.status_code = 400

            return response

        if user_otp == data["otp"]:
            existing_user = User.objects.filter(
                username=data["email"]
            ).first()

            if existing_user:

                request.session.pop("signup_data", None)

                messages.error(
                    request,
                    "An account with this email already exists."
                )

                return redirect("login")

            parts = data["name"].split()
            first = parts[0]
            last = " ".join(parts[1:]) if len(parts) > 1 else ""

            user = User.objects.create_user(
                username=data["email"],
                email=data["email"],
                password=data["password"],
                first_name=first,
                last_name=last,
            )

            referral_code = data.get("referral_code")

            if referral_code:

                referrer = User.objects.filter(
                    referral_code=referral_code
                ).first()

                if referrer and referrer.id != user.id:

                    user.referred_by = referrer
                    user.save()
            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend",
            )
            del request.session["signup_data"]

            messages.success(
                request,
                "Welcome to Westral Fashion. Account created successfully."
            )

            return redirect("home")
        else:

            messages.error(
                request,
                "Invalid OTP"
            )

            expiry_time = timezone.datetime.fromisoformat(
                data["otp_expiry"]
            )

            remaining_seconds = max(
                0,
                int((expiry_time - timezone.now()).total_seconds())
            )

            response = render(
                request,
                "signup_verify.html",
                {
                    "remaining_seconds": remaining_seconds,
                    "otp_expiry": data.get("otp_expiry"),
                }
            )
            response.status_code = 400

            return response
        
    data = request.session.get("signup_data")

    remaining_seconds = 0

    if data and data.get("otp_expiry"):

        expiry_time = timezone.datetime.fromisoformat(
            data["otp_expiry"]
        )

        remaining_seconds = max(
            0,
            int((expiry_time - timezone.now()).total_seconds())
        )
        

    return render(
        request,
        "signup_verify.html",
        {
            "otp_image": "https://your-image-url.com/image.jpg",
            "remaining_seconds": remaining_seconds,
            "otp_expiry": data.get("otp_expiry") if data else "",
        }
    )

@never_cache
def login_view(request):

    if request.user.is_authenticated:

        return redirect("home")

    if request.method == "POST":

        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        try:
            validate_email(email)
        except ValidationError:
            messages.error(
                request,
                "Please enter a valid email address.",
                extra_tags="login",
            )
            return render(request, "login.html", {"email": email})
        remember = request.POST.get("remember")

        context = {"email": email}

        if not email:
            messages.error(request, "Email is required.", extra_tags="login")
            return render(request, "login.html", context)

        if not password:
            messages.error(request, "Password is required.", extra_tags="login")
            return render(request, "login.html", context)

        user = authenticate(request, username=email, password=password)

        if user:

            if user.is_staff or user.is_superuser:
                messages.error(request, "Admin cannot login here.", extra_tags="login")
                return render(request, "login.html", context)

            if user.is_blocked:
                messages.error(
                    request,
                    "Your account has been blocked by admin.",
                    extra_tags="login",
                )
                return render(request, "login.html", context)

            login(request, user)
            request.session.set_expiry(60 * 60 * 24 * 30 if remember else 0)
            messages.success(
                request, f"Welcome back, {user.first_name}!", extra_tags="login"
            )
            return redirect("home")

        else:
            messages.error(request, "Invalid email or password", extra_tags="login")
            return redirect("login")

    return render(request, "login.html")


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home_view(request):

    latest_purchased_products = (
        Product.objects.filter(
            variants__orderitem__order__payment_status="Paid",
            is_active=True,
            is_deleted=False,
        )
        .distinct()
        .order_by("-variants__orderitem__created_at")[:4]
    )

    categories = Category.objects.filter(
        is_active=True,
        category_name__in=["Winter Wear", "Kurthas", "Western Wear", "Saree"],
    )

    context = {
        "latest_purchased_products": latest_purchased_products,
        "categories": categories,
    }

    return render(request, "homepage.html", context)


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")


def _send_otp(request, email):
    otp = str(random.randint(100000, 999999))

    expiry = time.time() + 60


    request.session["reset_otp"] = otp
    request.session["reset_email"] = email
    request.session["otp_expiry"] = expiry
    request.session["otp_verified"] = False

    send_mail(
        subject="Westral Fashion — Password Reset OTP",
        message=(
            f"Your OTP for password reset is: {otp}\n\n"
            f"This code expires in 1 minute. Do not share it."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if not User.objects.filter(email=email).exists():

            response = render(
                request,
                "forgot_password.html",
                {"error": "Email not found"}
            )

            response.status_code = 400

            return response
        _send_otp(request, email)

        return redirect("verify_otp")

    return render(request, "forgot_password.html")


def resend_otp(request):
    email = request.session.get("reset_email")

    if not email:
        return redirect("forgot_password")

    _send_otp(request, email)

    request.session["otp_message"] = "New OTP sent successfully"

    return redirect("verify_otp")


@never_cache
def verify_otp(request):
    otp_message = request.session.pop("otp_message", None)
    error = None

    if request.method == "POST":

        entered_otp = "".join(
            [request.POST.get(f"otp{i}", "") for i in range(1, 7)]
        ).strip()

        session_otp = request.session.get("reset_otp")
        expiry = request.session.get("otp_expiry")

        if len(entered_otp) != 6:
            error = "Enter complete OTP"

        elif not session_otp or not expiry:
            error = "Session expired. Please try again."

        else:

            try:
                expiry = float(expiry)
            except:

                error = "Invalid session data. Please resend OTP."
                return render(
                    request,
                    "verify_otp.html",
                    {"otp_message": otp_message, "error": error},
                )

            if time.time() > expiry:

                request.session.pop("reset_otp", None)
                request.session.pop("otp_expiry", None)

                error = "OTP expired. Please click Resend OTP."

            elif entered_otp != session_otp:
                error = "Invalid OTP"

            else:

                request.session["otp_verified"] = True

                request.session.pop("reset_otp", None)
                request.session.pop("otp_expiry", None)

                return redirect("reset_password")
            
    remaining_seconds = 0

    expiry = request.session.get("otp_expiry")

    if expiry:

        try:

            remaining_seconds = max(
                0,
                int(float(expiry) - time.time())
            )
            print("REMAINING =", remaining_seconds)

        except:

            remaining_seconds = 0    
            

    response = render(
        request,
        "verify_otp.html",
        {
            "otp_message": otp_message,
            "error": error,
            "remaining_seconds": remaining_seconds,
        }
    )

    if error:
        response.status_code = 400

    return response

@never_cache
def reset_password(request):

    if not request.session.get("reset_email") or not request.session.get(
        "otp_verified"
    ):
        return redirect("forgot_password")

    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        email = request.session.get("reset_email")

        if not password or not confirm_password:
            messages.error(request, "Both fields are required.")
            return render(request, "reset_password.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "reset_password.html")

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, "reset_password.html")

        try:
            user = User.objects.get(email=email)
            user.set_password(password)
            user.save()
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("forgot_password")

        request.session.flush()

        messages.success(request, "Password reset successfully!")
        return redirect("login")

    response = render(request, "reset_password.html")

    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response


def navbar_search(request):

    query = request.GET.get("q", "").strip()

    products = []

    if query:

        variants = (
            Variant.objects.filter(
                Q(product__product_name__icontains=query)
                | Q(product__category__category_name__icontains=query)
                | Q(color__color_name__icontains=query)
                | Q(size__size_name__icontains=query),
                is_deleted=False,
                is_active=True,
                product__is_deleted=False,
                product__category__is_deleted=False,
                product__category__is_active=True,
            )
            .select_related("product", "product__category", "color", "size")
            .prefetch_related("images")
            .distinct()[:8]
        )


        for variant in variants:

            image = variant.images.first()

            products.append(
                {
                    "id": variant.product.id,
                    "name": variant.product.product_name,
                    "price": str(variant.price),
                    "image": (image.image.url if image and image.image else ""),
                    "url": reverse("product_details", args=[variant.product.id]),
                }
            )

    return JsonResponse({"products": products})


@login_required
def referral_page(request):

    referral_link = request.build_absolute_uri(
        f"/signup/?ref={request.user.referral_code}"
    )

    referrals = request.user.referrals.all()

    show_reward_modal = request.user.show_referral_popup

    if show_reward_modal:

        request.user.show_referral_popup = False

        request.user.save()

    context = {
        "referral_link": referral_link,
        "referrals": referrals,
        "show_reward_modal": show_reward_modal,
    }

    return render(request, "referral.html", context)

@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup_resend_otp(request):

    data = request.session.get("signup_data")

    if not data:
        messages.error(request, "Signup session expired. Please sign up again.")
        return redirect("signup")

    last_sent = request.session.get("otp_sent_time")

    if last_sent:

        elapsed = time.time() - last_sent

        if elapsed < 60:

            messages.error(
                request,
                f"Please wait {int(60 - elapsed)} seconds before requesting another OTP."
            )

            return redirect("signup_verify")

    otp = str(random.randint(100000, 999999))

    expiry = timezone.now() + timedelta(minutes=1)

    data["otp"] = otp
    data["otp_expiry"] = expiry.isoformat()

    request.session["signup_data"] = data
    request.session["otp_sent_time"] = time.time()

    send_mail(
        "Your OTP Code",
        f"Your OTP is {otp}",
        settings.DEFAULT_FROM_EMAIL,
        [data["email"]],
        fail_silently=False,
    )

    messages.success(
        request,
        "New OTP sent successfully."
    )

    return redirect("signup_verify")



def custom_404(request, exception):
    return render(request, "404.html", status=404)