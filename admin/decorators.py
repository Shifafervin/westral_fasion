from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):

    def wrapper(request, *args, **kwargs):

        # ================= NOT LOGGED IN =================

        if not request.user.is_authenticated:

            messages.error(

                request,

                "Please login first"

            )

            return redirect("admin_login")

        # ================= NOT ADMIN =================

        if not (

            request.user.is_staff

            and

            request.user.is_superuser

        ):

            messages.error(

                request,

                "You are not authorized to access admin panel."

            )

            return redirect("home")

        # ================= BLOCKED =================

        if request.user.is_blocked:

            messages.error(

                request,

                "Your account is blocked."

            )

            return redirect("home")

        return view_func(

            request,

            *args,

            **kwargs

        )

    return wrapper