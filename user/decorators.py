from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def user_required(view_func):

    @login_required(login_url="login")

    def wrapper(request, *args, **kwargs):

        if (

            request.user.is_staff

            or

            request.user.is_superuser

        ):

            return redirect("admin_dashboard")

        return view_func(

            request,

            *args,

            **kwargs

        )

    return wrapper