from django.shortcuts import render
from decimal import Decimal
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.timezone import now
from admin.admin_coupon.models import Coupon
from admin.admin_orders.models import Wallet, WalletTransaction
from user.decorators import user_required
from django.conf import settings
from django.http import JsonResponse
import json
import razorpay
from django.core.paginator import Paginator
from admin.admin_orders.models import Order
from user.user_products.models import Cart


@user_required
def apply_coupon(request):
    print("APPLY COUPON VIEW HIT")

    if request.method != "POST":

        return redirect("checkout_page")

    coupon_code = request.POST.get("coupon_code", "").strip()

    print("Entered Coupon:", coupon_code)

    coupon = Coupon.objects.filter(
        code__iexact=coupon_code, is_active=True, is_deleted=False
    ).first()

    print("Coupon Found:", coupon)

    if not coupon_code:

        messages.error(request, "Please enter a coupon code", extra_tags="toast")

        return redirect("checkout_page")

    # ================= ALREADY APPLIED =================

    if request.session.get("coupon_id"):

        messages.error(request, "A coupon is already applied", extra_tags="toast")

        return redirect("checkout_page")

    # ================= COUPON EXISTS =================

    coupon = Coupon.objects.filter(
        code__iexact=coupon_code, is_active=True, is_deleted=False
    ).first()

    if not coupon:

        messages.error(request, "Invalid coupon code", extra_tags="toast")

        return redirect("checkout_page")

    # ================= EXTRA SAFETY =================

    if not coupon.is_active:

        messages.error(request, "This coupon is inactive", extra_tags="toast")

        return redirect("checkout_page")

    if coupon.is_deleted:

        messages.error(request, "This coupon is unavailable", extra_tags="toast")

        return redirect("checkout_page")

    # ================= DATE VALIDATION =================

    today = now().date()

    if not (coupon.valid_from <= today <= coupon.valid_to):

        messages.error(request, "Coupon expired or inactive", extra_tags="toast")

        return redirect("checkout_page")

    # ================= CART VALIDATION =================

    cart = request.user.cart

    if not cart:

        messages.error(request, "Cart not found", extra_tags="toast")

        return redirect("cart")

    cart_items = cart.items.all()

    if not cart_items.exists():

        messages.error(request, "Your cart is empty", extra_tags="toast")

        return redirect("cart")

    # ================= SUBTOTAL =================

    subtotal = Decimal("0")

    for item in cart_items:

        subtotal += item.variant.price * item.quantity

    # ================= MINIMUM PURCHASE =================

    if subtotal < coupon.minimum_purchase_amount:

        messages.error(
            request,
            f"Minimum purchase amount is ₹{coupon.minimum_purchase_amount}",
            extra_tags="toast",
        )

        return redirect("checkout_page")

    # ================= TOTAL USAGE LIMIT =================

    if coupon.used_count >= coupon.total_usage_limit:

        messages.error(request, "Coupon usage limit exceeded", extra_tags="toast")

        return redirect("checkout_page")

    user_usage_count = Order.objects.filter(
        user=request.user, coupon=coupon, payment_status="SUCCESS"
    ).count()

    if user_usage_count >= coupon.usage_limit_per_user:

        messages.error(
            request,
            "You have already reached the usage limit for this coupon",
            extra_tags="toast",
        )

        return redirect("checkout_page")

    # ================= STORE SESSION =================

    request.session["coupon_id"] = coupon.id

    print("PAYMENT FROM POST:", request.POST.get("payment_method"))

    print("ADDRESS FROM POST:", request.POST.get("selected_address"))

    request.session["selected_payment_method"] = request.POST.get(
        "payment_method", "COD"
    )

    request.session["selected_address"] = request.POST.get("selected_address")

    print("SESSION PAYMENT:", request.session.get("selected_payment_method"))

    print("SESSION ADDRESS:", request.session.get("selected_address"))

    # ================= SUCCESS =================

    messages.success(
        request, f"Coupon '{coupon.code}' applied successfully", extra_tags="toast"
    )

    return redirect("checkout_page")


@user_required
def remove_coupon(request):

    if "coupon_id" in request.session:

        del request.session["coupon_id"]

        messages.success(request, "Coupon removed successfully")

    return redirect("checkout_page")


@user_required
def wallet_page(request):

    wallet, created = Wallet.objects.get_or_create(user=request.user)

    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by(
        "-created_at"
    )

    paginator = Paginator(transactions, 5)

    page_number = request.GET.get("page")

    transactions = paginator.get_page(page_number)

    context = {"wallet": wallet, "transactions": transactions}

    return render(request, "wallet.html", context)


@user_required
def create_wallet_razorpay_order(request):

    if request.method == "POST":

        data = json.loads(request.body)

        amount = int(data.get("amount")) * 100

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        payment = client.order.create(
            {"amount": amount, "currency": "INR", "payment_capture": 1}
        )

        return JsonResponse(
            {
                "success": True,
                "key": settings.RAZORPAY_KEY_ID,
                "amount": payment["amount"],
                "razorpay_order_id": payment["id"],
            }
        )

    return JsonResponse({"success": False})


@user_required
def wallet_payment_success(request):

    razorpay_payment_id = request.GET.get("payment_id")

    razorpay_order_id = request.GET.get("order_id")

    razorpay_signature = request.GET.get("signature")

    amount = request.GET.get("amount")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:

        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

    except:

        context = {
            "wallet": wallet,
            "amount": recharge_amount,
            "payment_id": razorpay_payment_id,
        }

        return render(request, "wallet_success.html", context)

    wallet, created = Wallet.objects.get_or_create(user=request.user)

    recharge_amount = Decimal(amount)

    wallet.balance += recharge_amount

    wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type="Credit",
        status="Completed",
        amount=recharge_amount,
        description="Wallet Recharge",
    )

    context = {
        "wallet": wallet,
        "amount": recharge_amount,
        "payment_id": razorpay_payment_id,
    }

    return render(request, "wallet_success.html", context)


@user_required
def wallet_payment_failed(request):

    return render(request, "wallet_fail.html")
