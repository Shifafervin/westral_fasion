from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Address
from user.decorators import user_required
import re
from django.core.exceptions import ValidationError


@login_required(login_url='login')
def address_page(request):
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')

    return render(request, 'address.html', {
        'addresses': addresses
    })


@user_required
def add_address(request):

    if request.method == "POST":

        full_name = request.POST.get(

            "full_name",
            ""

        ).strip()

        phone = request.POST.get(

            "phone",
            ""

        ).strip()

        pincode = request.POST.get(

            "pincode",
            ""

        ).strip()

        state = request.POST.get(

            "state",
            ""

        ).strip()

        city = request.POST.get(

            "city",
            ""

        ).strip()

        country = request.POST.get(

            "country",
            ""

        ).strip()

        address_line = request.POST.get(

            "address_line",
            ""

        ).strip()

        address_type = request.POST.get(

            "address_type",
            "home"

        ).strip()

        is_default = request.POST.get(

            "is_default"

        ) == "on"

    

        if not all([

            full_name,
            phone,
            pincode,
            state,
            city,
            country,
            address_line

        ]):

            messages.error(

                request,
                "All fields are required"

            )

            return render(
                request,
                "add_address.html",
                {
                    "form_data": request.POST
                }
            )


        if is_default:

            Address.objects.filter(
                user=request.user,
                is_default=True
            ).update(
                is_default=False
            )

        try:

            address = Address.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                pincode=pincode,
                state=state,
                city=city,
                country=country,
                address_line=address_line,
                address_type=address_type,
                is_default=is_default
            )

            request.session["selected_address"] = address.id

        except ValidationError as e:

            for errors in e.message_dict.values():

                for error in errors:

                    messages.error(
                        request,
                        error
                    )

            return render(
                request,
                "add_address.html",
                {
                    "form_data": request.POST
                }
            )
        messages.success(

            request,
            "Address added successfully"

        )

        next_page = request.GET.get("next") or request.POST.get("next")

        if next_page == "checkout":
            return redirect("checkout_page")

        return redirect("address_details:address_view")

    return render(
        request,
        "add_address.html",
        {
            "form_data": {}
        }
    )

@user_required
def delete_address(request, id):

    address = get_object_or_404(

        Address,

        id=id,

        user=request.user

    )

    if request.method == "POST":

        address.delete()

        messages.success(

            request,

            "Address deleted successfully"

        )

        return redirect(

            "address_details:address_view"

        )

    return render(

        request,

        "delete_address.html",

        {

            "address": address

        }

    )




@user_required
def edit_address(request, id):

    address = get_object_or_404(
        Address,
        id=id,
        user=request.user
    )

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        city = request.POST.get(
            "city",
            ""
        ).strip()

        pincode = request.POST.get(
            "pincode",
            ""
        ).strip()

        state = request.POST.get(
            "state",
            ""
        ).strip()

        country = request.POST.get(
            "country",
            ""
        ).strip()

        address_line = request.POST.get(
            "address_line",
            ""
        ).strip()

        address_type = request.POST.get(
            "address_type",
            "home"
        ).strip()

        is_default = request.POST.get(
            "is_default"
        ) == "on"

        if not all([
            full_name,
            phone,
            city,
            pincode,
            state,
            country,
            address_line
        ]):

            messages.error(
                request,
                "All fields are required"
            )

            return render(
                request,
                "edit_address.html",
                {
                    "address": address,
                    "form_data": request.POST
                }
            )

        address.full_name = full_name
        address.phone = phone
        address.city = city
        address.pincode = pincode
        address.state = state
        address.country = country
        address.address_line = address_line
        address.address_type = address_type
        address.is_default = is_default

        try:

            address.save()
            request.session["selected_address"] = address.id

            if is_default:

                Address.objects.filter(
                    user=request.user,
                    is_default=True
                ).exclude(
                    id=address.id
                ).update(
                    is_default=False
                )

                address.is_default = True
                address.save()

        except ValidationError as e:

            for errors in e.message_dict.values():

                for error in errors:

                    messages.error(
                        request,
                        error
                    )

            return render(
                request,
                "edit_address.html",
                {
                    "address": address,
                    "form_data": request.POST
                }
            )

        messages.success(
            request,
            "Address updated successfully"
        )

        next_page = request.GET.get("next") or request.POST.get("next")

        if next_page == "checkout":

            return redirect("checkout_page")

        return redirect("address_details:address_view")

    return render(
        request,
        "edit_address.html",
        {
            "address": address
        }
    )