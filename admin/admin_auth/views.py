from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login , logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator
from admin.decorators import admin_required
from django.db.models import (
    Q,
    Count
)
User = get_user_model()

@never_cache
def admin_login(request):

    # ================= ALREADY LOGGED IN =================

    if request.user.is_authenticated:

        if (

            request.user.is_staff

            and

            request.user.is_superuser

        ):

            return redirect("admin_dashboard")

        return redirect("home")

    # ================= LOGIN =================

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(

            request,

            username=email,

            password=password

        )

        if not user:

            messages.error(

                request,

                "Invalid email or password"

            )

            return redirect("admin_login")

        # ================= ADMIN CHECK =================

        if not (

            user.is_staff

            and

            user.is_superuser

        ):

            messages.error(

                request,

                "You are not authorized to access admin panel."

            )

            return redirect("admin_login")

        # ================= BLOCK CHECK =================

        if user.is_blocked:

            messages.error(

                request,

                "Your account is blocked."

            )

            return redirect("admin_login")

        # ================= LOGIN =================

        login(request, user)

        messages.success(

            request,

            "Login successful"

        )

        return redirect(

            "admin_dashboard"

        )

    return render(

        request,

        "admin_login.html"

    )


@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@admin_required
def admin_dashboard(request):
    return render(request, "admin_dashboard.html")

def admin_logout(request):
    logout(request)
    return redirect("admin_login")

@admin_required
def user_management(request):

    # ================= SEARCH =================

    query = request.GET.get(
        "q",
        ""
    ).strip()

    # ================= STATUS FILTER =================

    status = request.GET.get(
        "status",
        ""
    )

    # ================= QUERYSET =================

    users_list = User.objects.filter(

        is_staff=False

    ).order_by("-id")

    # ================= SEARCH =================

    if query:

        users_list = users_list.filter(

            Q(username__icontains=query) |

            Q(email__icontains=query) |

            Q(first_name__icontains=query) |

            Q(last_name__icontains=query)

        )

    # ================= STATUS FILTER =================

    if status == "active":

        users_list = users_list.filter(
            is_blocked=False
        )

    elif status == "blocked":

        users_list = users_list.filter(
            is_blocked=True
        )

    # ================= STATS =================

    total_users = User.objects.filter(
        is_staff=False
    ).count()

    active_users = User.objects.filter(

        is_staff=False,
        is_blocked=False

    ).count()

    blocked_users = User.objects.filter(

        is_staff=False,
        is_blocked=True

    ).count()

    # ================= PAGINATION =================

    paginator = Paginator(
        users_list,
        5
    )

    page_number = request.GET.get("page")

    users = paginator.get_page(
        page_number
    )

    context = {

        "users": users,

        "query": query,

        "selected_status": status,

        "total_users": total_users,

        "active_users": active_users,

        "blocked_users": blocked_users,

    }

    return render(

        request,

        "user_management.html",

        context

    )

@admin_required
def toggle_user_status(request, user_id):

    user = get_object_or_404(
        User,
        id=user_id
    )

    # PREVENT STAFF/SUPERUSER BLOCK
    if user.is_staff or user.is_superuser:

        messages.error(
            request,
            "Admin users cannot be blocked.",
            extra_tags="toast"
        )

        return redirect("user_management")

    # PREVENT SELF BLOCK
    if request.user.id == user.id:

        messages.error(
            request,
            "You cannot block your own account.",
            extra_tags="toast"
        )

        return redirect("user_management")

    # TOGGLE STATUS
    user.is_blocked = not user.is_blocked
    user.save()

    # SUCCESS MESSAGE
    if user.is_blocked:

        messages.success(
            request,
            f"{user.username} blocked successfully.",
            extra_tags="toast"
        )

    else:

        messages.success(
            request,
            f"{user.username} unblocked successfully.",
            extra_tags="toast"
        )

    return redirect("user_management")