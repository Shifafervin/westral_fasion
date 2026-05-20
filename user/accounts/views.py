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
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
import time

User = get_user_model()



def validate_password_strength(password):

    if len(password) < 8:
        return "Password must be at least 8 characters."

    if not re.search(r'[A-Z]', password):
        return "Add at least one uppercase letter."

    if not re.search(r'[a-z]', password):
        return "Add at least one lowercase letter."

    if not re.search(r'\d', password):
        return "Add at least one number."

    if not re.search(r'[!@#$%^&*]', password):
        return "Add at least one special character (!@#$%^&*)."

    return None



def signup_view(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm_password", "")

        errors = {}

    
        if not name:

            errors["name"] = "Full name is required"

        elif len(name) < 3:

            errors["name"] = "Name must be at least 3 characters"

        elif not re.match(r"^[A-Za-z ]+$", name):

            errors["name"] = "Name must contain only letters"

        elif name.strip().count(" ") < 1:

            errors["name"] = "Enter first and last name"
            

        if not email:
            errors["email"] = "Email is required"

        if not password:
            errors["password"] = "Password is required"

        if password != confirm:
            errors["confirm_password"] = "Passwords do not match"

    
        password_error = validate_password_strength(password)
        if password_error:
            errors["password"] = password_error

    
        if User.objects.filter(email=email).exists():
            errors["email"] = "Email already exists"

    
        if errors:
            return render(request, "signup.html", {
                "errors": errors,
                "name": name,
                "email": email
            })

        
        otp = str(random.randint(100000, 999999))

        
        request.session['signup_data'] = {
            "name": name,
            "email": email,
            "password": password,
            "otp": otp
        }

    
        request.session['otp_message'] = f"A new OTP has been sent to {email}"

        
        send_mail(
            "Your OTP Code",
            f"Your OTP is {otp}",
            "your_email@gmail.com",
            [email],
            fail_silently=False,
        )

        return redirect("signup_verify")   


    return render(request, "signup.html")


def signup_verify(request):

    if request.method == "POST":

        
        user_otp = ''.join([
            request.POST.get(f'otp{i}', '') for i in range(1, 7)
        ])

    
        if len(user_otp) != 6:
            messages.error(request, "Enter complete OTP")
            return redirect("signup_verify")

        data = request.session.get('signup_data')

        if not data:
            messages.error(request, "Session expired. Signup again.")
            return redirect("signup")

        if user_otp == data['otp']:

        
            parts = data['name'].split()
            first = parts[0]
            last = ' '.join(parts[1:]) if len(parts) > 1 else ''

        
            user = User.objects.create_user(
                username=data['email'],
                email=data['email'],
                password=data['password'],
                first_name=first,
                last_name=last
            )

    
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            
            del request.session['signup_data']

            messages.success(request, "Account created successfully")

            return redirect("home")

        else:
            messages.error(request, "Invalid OTP")
            return redirect("signup_verify")

    return render(request, "signup_verify.html")


@never_cache
def login_view(request):

    if request.user.is_authenticated:

        return redirect("home")

    if request.method == 'POST':

        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember')

        context = {'email': email}

        if not email:
            messages.error(
                request,
                "Email is required.",
                extra_tags="login"
            )
            return render(request, 'login.html', context)

        if not password:
            messages.error(request, "Password is required.",extra_tags="login")
            return render(request, 'login.html', context)

        user = authenticate(request, username=email, password=password)

        if user:

    
            if user.is_staff or user.is_superuser:
                messages.error(request, "Admin cannot login here.",extra_tags="login")
                return render(request, 'login.html', context)


            if user.is_blocked:
                messages.error(request, "Your account has been blocked by admin.",extra_tags="login")
                return render(request, 'login.html', context)

    
            login(request, user)
            request.session.set_expiry(60 * 60 * 24 * 30 if remember else 0)
            messages.success(
                request,
                f"Welcome back, {user.first_name}!",
                extra_tags="login"
            )
            return redirect('home')

        else:
            messages.error(request, "Invalid email or password",extra_tags="login")
            return redirect('login')

    return render(request, 'login.html')



@never_cache
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def home_view(request):

    return render(
        request,
        "homepage.html"
    )

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')



def _send_otp(request, email):
    otp = str(random.randint(100000, 999999))

    expiry = time.time() + 60   


    print("EXPIRY TYPE:", type(expiry), expiry)

    request.session["reset_otp"]    = otp
    request.session["reset_email"]  = email
    request.session["otp_expiry"]   = expiry
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
    if request.method == 'POST':
        email = request.POST.get('email')

        if not User.objects.filter(email=email).exists():
            return render(request, 'forgot_password.html', {
                "error": "Email not found"
            })


        _send_otp(request, email)

        return redirect('verify_otp')

    return render(request, 'forgot_password.html')


def resend_otp(request):
    email = request.session.get("reset_email")

    if not email:
        return redirect("forgot_password")

    _send_otp(request, email)


    request.session['otp_message'] = "New OTP sent successfully"

    return redirect("verify_otp")



@never_cache
def verify_otp(request):
    otp_message = request.session.pop('otp_message', None)
    error = None

    if request.method == 'POST':

        entered_otp = ''.join([
            request.POST.get(f'otp{i}', '') for i in range(1, 7)
        ]).strip()

        session_otp = request.session.get('reset_otp')
        expiry = request.session.get('otp_expiry')


        if len(entered_otp) != 6:
            error = "Enter complete OTP"


        elif not session_otp or not expiry:
            error = "Session expired. Please try again."

        else:
        
            try:
                expiry = float(expiry)
            except:
            
                error = "Invalid session data. Please resend OTP."
                return render(request, 'verify_otp.html', {
                    "otp_message": otp_message,
                    "error": error
                })

        
            if time.time() > expiry:
                error = "OTP expired. Please resend."


            elif entered_otp != session_otp:
                error = "Invalid OTP"

            else:
            
                request.session['otp_verified'] = True

                request.session.pop('reset_otp', None)
                request.session.pop('otp_expiry', None)

                return redirect('reset_password')

    return render(request, 'verify_otp.html', {
        "otp_message": otp_message,
        "error": error
    })


@never_cache
def reset_password(request):

    
    if not request.session.get("reset_email") or not request.session.get("otp_verified"):
        return redirect("forgot_password")

    if request.method == "POST":
        password         = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        email            = request.session.get("reset_email")

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


    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response

from user.user_products.models import Variant

from django.http import JsonResponse

from django.db.models import Q

from django.urls import reverse


def navbar_search(request):

    query = request.GET.get(

        "q",

        ""

    ).strip()

    products = []

    if query:

        variants = Variant.objects.filter(

            Q(
                product__product_name__icontains=query
            ) |

            Q(
                product__category__category_name__icontains=query
            ) |

            Q(
                color__color_name__icontains=query
            ) |

            Q(
                size__size_name__icontains=query
            ),

            is_deleted=False,

            is_active=True,

            product__is_deleted=False,

            product__category__is_deleted=False,

            product__category__is_active=True

        ).select_related(

            "product",

            "product__category",

            "color",

            "size"

        ).prefetch_related(

            "images"

        ).distinct()[:8]

        print(

            variants

        )

        for variant in variants:

            image = variant.images.first()

            products.append({

                "id": variant.product.id,

                "name": variant.product.product_name,

                "price": str(

                    variant.price

                ),

                "image": (

                    image.image.url

                    if image and image.image

                    else ""

                ),

                "url": reverse(

                    "product_details",

                    args=[

                        variant.product.id

                    ]

                )

            })

    return JsonResponse({

        "products": products

    })