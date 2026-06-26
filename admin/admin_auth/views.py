from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from admin.decorators import admin_required
from django.db.models import Q
from user.user_orders.models import Order, OrderItem
from django.db.models import Sum
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from django.db.models import Sum
from django.db.models import F
from admin.admin_product.models import Variant

User = get_user_model()


@never_cache
def admin_login(request):


    if request.user.is_authenticated:

        if request.user.is_staff and request.user.is_superuser:

            return redirect("admin_dashboard")

        return redirect("home")


    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if not user:

            messages.error(request, "Invalid email or password")

            return redirect("admin_login")

    

        if not (user.is_staff and user.is_superuser):

            messages.error(request, "You are not authorized to access admin panel.")

            return redirect("admin_login")

        if user.is_blocked:

            messages.error(request, "Your account is blocked.")

            return redirect("admin_login")


        login(request, user)

        messages.success(request, "Login successful")

        return redirect("admin_dashboard")

    return render(request, "admin_login.html")


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def admin_dashboard(request):

    sales_orders = Order.objects.filter(
        payment_status="SUCCESS", order_status="Delivered"
    ).exclude(return_status__in=["Returned", "Refunded"])

    total_revenue = sales_orders.aggregate(total=Sum("total_amount"))["total"] or 0

    total_orders = sales_orders.count()

    pending_orders = Order.objects.filter(order_status="Pending").count()

    total_customers = User.objects.filter(is_superuser=False).count()

    today = timezone.now().date()

    week_start = today - timedelta(days=today.weekday())

    weekly_data = []

    labels = []

    for i in range(7):

        day = week_start + timedelta(days=i)

        revenue = (
            sales_orders.filter(created_at__date=day).aggregate(
                total=Sum("total_amount")
            )["total"]
            or 0
        )

        weekly_data.append(float(revenue))

        labels.append(day.strftime("%a").upper())


    best_selling_products = (
        OrderItem.objects.filter(
            order__payment_status="SUCCESS", order__order_status="Delivered"
        )
        .exclude(order__return_status__in=["Returned", "Refunded"])
        .values("variant__product__product_name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:10]
    )

    best_selling_categories = (
        OrderItem.objects.filter(
            order__payment_status="SUCCESS", order__order_status="Delivered"
        )
        .exclude(order__return_status__in=["Returned", "Refunded"])
        .values("variant__product__category__category_name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:10]
    )
    recent_orders = Order.objects.select_related("user").order_by("-created_at")[:10]

    low_stock_products = (
        Variant.objects.filter(
            is_active=True, is_deleted=False, stock__lte=F("low_stock_threshold")
        )
        .select_related("product")
        .order_by("stock")[:10]
    )

    current_month_revenue = (
        sales_orders.filter(
            created_at__year=today.year, created_at__month=today.month
        ).aggregate(total=Sum("total_amount"))["total"]
        or 0
    )

    previous_month = today.replace(day=1) - timedelta(days=1)
    previous_month_revenue = (
        sales_orders.filter(
            created_at__year=previous_month.year, created_at__month=previous_month.month
        ).aggregate(total=Sum("total_amount"))["total"]
        or 0
    )

    revenue_growth = 0

    if previous_month_revenue:

        revenue_growth = round(
            (current_month_revenue - previous_month_revenue)
            / previous_month_revenue
            * 100,
            2,
        )
        current_month_orders = sales_orders.filter(
            created_at__year=today.year, created_at__month=today.month
        ).count()

        previous_month_orders = sales_orders.filter(
            created_at__year=previous_month.year, created_at__month=previous_month.month
        ).count()

        orders_growth = 0

        if previous_month_orders:

            orders_growth = round(
                (current_month_orders - previous_month_orders)
                / previous_month_orders
                * 100,
                2,
            )

    context = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_customers": total_customers,
        "weekly_labels": labels,
        "weekly_data": weekly_data,
        "best_selling_products": best_selling_products,
        "best_selling_categories": best_selling_categories,
        "recent_orders": recent_orders,
        "low_stock_products": low_stock_products,
        "revenue_growth": revenue_growth,
        "orders_growth": orders_growth,
    }
    return render(request, "admin_dashboard.html", context)


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_logout(request):
    logout(request)
    return redirect("admin_login")


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def user_management(request):

    query = request.GET.get("q", "").strip()

    status = request.GET.get("status", "")

    users_list = User.objects.filter(is_staff=False).order_by("-id")

    if query:

        users_list = users_list.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )

    if status == "active":

        users_list = users_list.filter(is_blocked=False)

    elif status == "blocked":

        users_list = users_list.filter(is_blocked=True)

    total_users = User.objects.filter(is_staff=False).count()

    active_users = User.objects.filter(is_staff=False, is_blocked=False).count()

    blocked_users = User.objects.filter(is_staff=False, is_blocked=True).count()


    paginator = Paginator(users_list, 5)

    page_number = request.GET.get("page")

    users = paginator.get_page(page_number)

    context = {
        "users": users,
        "query": query,
        "selected_status": status,
        "total_users": total_users,
        "active_users": active_users,
        "blocked_users": blocked_users,
    }

    return render(request, "user_management.html", context)


@never_cache
@admin_required
@require_POST
def toggle_user_status(request, user_id):

    user = get_object_or_404(User, id=user_id)

    if user.is_staff or user.is_superuser:

        messages.error(request, "Admin users cannot be blocked.", extra_tags="toast")

        return redirect("user_management")

    if request.user.id == user.id:

        messages.error(
            request, "You cannot block your own account.", extra_tags="toast"
        )

        return redirect("user_management")

    user.is_blocked = not user.is_blocked
    user.save()

    if user.is_blocked:

        messages.success(
            request, f"{user.username} blocked successfully.", extra_tags="toast"
        )

    else:

        messages.success(
            request, f"{user.username} unblocked successfully.", extra_tags="toast"
        )

    return redirect("user_management")


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def sales_report(request):
    sales_orders = (
        Order.objects.filter(payment_status="SUCCESS", order_status="Delivered")
        .exclude(return_status__in=["Returned", "Refunded"])
        .prefetch_related("items")
        .select_related("user")
    )

    today = timezone.now().date()

    filter_type = request.GET.get("filter", "all")

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if start_date and end_date:

        if start_date > end_date:

            messages.error(request, "Start date cannot be greater than end date.")

            return redirect("sales_report")

    if start_date and end_date:

        sales_orders = sales_orders.filter(
            created_at__date__range=[start_date, end_date]
        )

    else:
        if filter_type == "all":

            pass
        if filter_type == "daily":

            sales_orders = sales_orders.filter(created_at__date=today)

        elif filter_type == "weekly":

            sales_orders = sales_orders.filter(
                created_at__date__gte=today - timedelta(days=6)
            )

        elif filter_type == "monthly":

            sales_orders = sales_orders.filter(
                created_at__year=today.year, created_at__month=today.month
            )

        elif filter_type == "yearly":

            sales_orders = sales_orders.filter(created_at__year=today.year)

    orders = sales_orders
    cancelled_orders = Order.objects.filter(order_status="Cancelled")

    returned_orders = Order.objects.filter(return_status__in=["Returned", "Refunded"])
    if start_date and end_date:

        cancelled_orders = cancelled_orders.filter(
            created_at__date__range=[start_date, end_date]
        )

        returned_orders = returned_orders.filter(
            created_at__date__range=[start_date, end_date]
        )

    else:

        if filter_type == "daily":

            cancelled_orders = cancelled_orders.filter(created_at__date=today)

            returned_orders = returned_orders.filter(created_at__date=today)

        elif filter_type == "weekly":

            cancelled_orders = cancelled_orders.filter(
                created_at__date__gte=today - timedelta(days=6)
            )

            returned_orders = returned_orders.filter(
                created_at__date__gte=today - timedelta(days=6)
            )

        elif filter_type == "monthly":

            cancelled_orders = cancelled_orders.filter(
                created_at__year=today.year, created_at__month=today.month
            )

            returned_orders = returned_orders.filter(
                created_at__year=today.year, created_at__month=today.month
            )

        elif filter_type == "yearly":

            cancelled_orders = cancelled_orders.filter(created_at__year=today.year)

            returned_orders = returned_orders.filter(created_at__year=today.year)

    chart_data = (
        orders.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Sum("total_amount"))
        .order_by("day")
    )

    chart_labels = [item["day"].strftime("%d %b") for item in chart_data]

    chart_values = [float(item["revenue"]) for item in chart_data]


    total_orders = orders.count()

    net_revenue = orders.aggregate(total=Sum("total_amount"))["total"] or 0

    coupon_discount = orders.aggregate(total=Sum("coupon_discount"))["total"] or 0

    offer_discount = orders.aggregate(total=Sum("offer_discount"))["total"] or 0

    gross_revenue = net_revenue + coupon_discount

    total_discount = coupon_discount + offer_discount

    total_revenue = gross_revenue

    returned_amount = returned_orders.aggregate(total=Sum("total_amount"))["total"] or 0

    cancelled_amount = (
        cancelled_orders.aggregate(total=Sum("total_amount"))["total"] or 0
    )

    total_products_sold = sum(
        item.quantity for order in orders for item in order.items.all()
    )

    now = timezone.now()

    base_orders = Order.objects.filter(
        payment_status="SUCCESS", order_status="Delivered"
    ).exclude(return_status__in=["Returned", "Refunded"])
    current_month_sales = (
        base_orders.filter(
            created_at__year=now.year, created_at__month=now.month
        ).aggregate(total=Sum("total_amount"))["total"]
        or 0
    )

    previous_month = now.replace(day=1) - timedelta(days=1)

    previous_month_sales = (
        base_orders.filter(
            created_at__year=previous_month.year, created_at__month=previous_month.month
        ).aggregate(total=Sum("total_amount"))["total"]
        or 0
    )

    growth = 0

    if previous_month_sales > 0:

        growth = round(
            ((current_month_sales - previous_month_sales) / previous_month_sales) * 100,
            2,
        )

    recent_transactions = Order.objects.select_related("user").order_by("-created_at")[
        :10
    ]

    if request.GET.get("export") == "pdf":

        response = HttpResponse(content_type="application/pdf")

        response["Content-Disposition"] = "attachment; " 'filename="sales_report.pdf"'

        doc = SimpleDocTemplate(response)

        styles = getSampleStyleSheet()

        elements = []

        elements.append(Paragraph("WESTRAL FASHION SALES REPORT", styles["Title"]))

        elements.append(Spacer(1, 20))

        elements.append(Paragraph(f"Total Orders : {total_orders}", styles["Normal"]))

        elements.append(
            Paragraph(f"Total Revenue : ₹{total_revenue}", styles["Normal"])
        )

        elements.append(Paragraph(f"Net Revenue : ₹{net_revenue}", styles["Normal"]))

        elements.append(Spacer(1, 20))

        data = [["Order ID", "Customer", "Status", "Payment", "Amount"]]

        for order in orders:

            data.append(
                [
                    str(order.order_id),
                    str(order.user.email),
                    str(order.order_status),
                    str(order.payment_method),
                    f"₹{order.total_amount}",
                ]
            )

        table = Table(data)

        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4B2D2D")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )

        elements.append(table)

        doc.build(elements)

        return response

    if request.GET.get("export") == "excel":

        workbook = Workbook()

        worksheet = workbook.active

        worksheet.title = "Sales Report"

        worksheet.append(["Order ID", "Customer", "Status", "Payment Method", "Amount"])
        from openpyxl.styles import Font

        for cell in worksheet[1]:

            cell.font = Font(bold=True)

        for order in orders:

            worksheet.append(
                [
                    str(order.order_id),
                    order.user.email,
                    order.order_status,
                    order.payment_method,
                    float(order.total_amount),
                ]
            )

        worksheet.append([])

        worksheet.append(["Total Orders", total_orders])

        worksheet.append(["Total Revenue", float(total_revenue)])

        worksheet.append(["Net Revenue", float(net_revenue)])

        worksheet.append(["Coupon Discount", float(coupon_discount)])

        worksheet.append(["Offer Discount", float(offer_discount)])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        response["Content-Disposition"] = 'attachment; filename="sales_report.xlsx"'

        workbook.save(response)

        return response


    paginator = Paginator(orders, 10)

    page_number = request.GET.get("page")

    orders = paginator.get_page(page_number)

    context = {
        "orders": orders,
        "recent_transactions": recent_transactions,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "net_revenue": net_revenue,
        "coupon_discount": coupon_discount,
        "offer_discount": offer_discount,
        "total_discount": total_discount,
        "cancelled_amount": cancelled_amount,
        "returned_amount": returned_amount,
        "growth": growth,
        "current_month_sales": current_month_sales,
        "previous_month_sales": previous_month_sales,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "start_date": start_date,
        "end_date": end_date,
        "filter_type": filter_type,
    }
    return render(request, "sales_report.html", context)
