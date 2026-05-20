from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Address
from user.decorators import user_required
import re

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
                "add_address.html"

            )



        if not re.match(

            r"^[A-Za-z ]+$",

            full_name

        ):

            messages.error(

                request,
                "Full name must contain only letters"

            )

            return render(

                request,
                "add_address.html"

            )

        if len(full_name) < 3:

            messages.error(

                request,
                "Full name is too short"

            )

            return render(

                request,
                "add_address.html"

            )


        if not phone.isdigit():

            messages.error(

                request,
                "Phone number must contain only digits"

            )

            return render(

                request,
                "add_address.html"

            )

        if len(phone) != 10:

            messages.error(

                request,

                "Phone number must be exactly 10 digits"

            )

            return render(

                request,

                "add_address.html",

                {

                    "form_data": request.POST

                }

            )
        if not pincode.isdigit():

            messages.error(

                request,
                "Pincode must contain only digits"

            )

            return render(

                request,
                "add_address.html"

            )

        if len(pincode) != 6:

            messages.error(

                request,
                "Pincode must be exactly 6 digits"

            )

            return render(

                request,
                "add_address.html"

            )


        if not re.match(

            r"^[A-Za-z ]+$",

            city

        ):

            messages.error(

                request,
                "City must contain only letters"

            )

            return render(

                request,
                "add_address.html"

            )


        if not re.match(

            r"^[A-Za-z ]+$",

            state

        ):

            messages.error(

                request,
                "State must contain only letters"

            )

            return render(

                request,
                "add_address.html"

            )



        if not re.match(

            r"^[A-Za-z ]+$",

            country

        ):

            messages.error(

                request,
                "Country must contain only letters"

            )

            return render(

                request,
                "add_address.html"

            )



        if len(address_line) < 10:

            messages.error(

                request,
                "Address is too short"

            )

            return render(

                request,
                "add_address.html"

            )



        if is_default:

            Address.objects.filter(

                user=request.user,
                is_default=True

            ).update(

                is_default=False

            )


        Address.objects.create(

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

        messages.success(

            request,
            "Address added successfully"

        )

        return redirect(

            "address_details:address_view"

        )

    return render(

        request,
        "add_address.html"

    )

def delete_address(request, id):

    address = Address.objects.filter(id=id, user=request.user).first()

    
    if not address:
        return redirect('address_details:address_view')

    if request.method == "POST":
        address.delete()
        return redirect('address_details:address_view')

    addresses = Address.objects.filter(user=request.user)

    return render(request, "delete_address.html", {
        "addresses": addresses
    })





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
            "HOME"

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

            return redirect(

                "address_details:edit_address",
                address.id

            )


        if not re.match(

            r"^[A-Za-z ]+$",

            full_name

        ):

            messages.error(

                request,
                "Full name must contain only letters"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )

        if len(full_name) < 3:

            messages.error(

                request,
                "Full name is too short"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )


        if not phone.isdigit():

            messages.error(

                request,
                "Phone number must contain only digits"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )

        if len(phone) != 10:

            messages.error(

                request,
                "Phone number must be exactly 10 digits"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )


        if not pincode.isdigit():

            messages.error(

                request,
                "Pincode must contain only digits"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )

        if len(pincode) != 6:

            messages.error(

                request,
                "Pincode must be exactly 6 digits"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )


        if not re.match(

            r"^[A-Za-z ]+$",

            city

        ):

            messages.error(

                request,
                "City must contain only letters"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )


        if not re.match(

            r"^[A-Za-z ]+$",

            state

        ):

            messages.error(

                request,
                "State must contain only letters"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )


        if not re.match(

            r"^[A-Za-z ]+$",

            country

        ):

            messages.error(

                request,
                "Country must contain only letters"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )


        if len(address_line) < 10:

            messages.error(

                request,
                "Address is too short"

            )

            return redirect(

                "address_details:edit_address",
                address.id

            )


        if is_default:

            Address.objects.filter(

                user=request.user,
                is_default=True

            ).exclude(

                id=address.id

            ).update(

                is_default=False

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

        address.save()

        messages.success(

            request,
            "Address updated successfully"

        )

        return redirect(

            "address_details:address_view"

        )

    return render(

        request,

        "edit_address.html",

        {

            "address": address

        }

    )