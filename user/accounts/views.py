from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


def signup_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", '').strip()
        email = request.POST.get("email", '').strip()
        password = request.POST.get("password", '').strip()
        confirm_password = request.POST.get("confirm_password", '').strip()

        if not all([full_name, email, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return redirect("signup")
        
        if len(full_name) < 4:
            messages.error(request,'length should be minimum 4') 
            return redirect("signup")
        
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request,"invalid email format") 
            return redirect("signup")

        try:
            validate_password(password)
        except ValidationError as e:
            for error in e:
                messages.error(request,error)
            return redirect("signup")       

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")


        existing_user=User.objects.filter(email=email).first()

        if existing_user:
            if existing_user.is_verified:
                messages.error(request,"email already existing")
                return render("signup")
            else:
                existing_user.full_name=full_name
                existing_user.set_password(password)
                existing_user.is_verified=False
                existing_user.save()
                user=existing_user
        else:
            User=User.objects.create_user(
                email=email
                full_name=full_name
                password=password
                is_verified=False
            )     

        request.session['otp_user_id']=user.id 
        request.session['otp_pupose']='signup' 

        otp_obj=generate_otp(user, purpose='signup') 
        send_otp_email(user,otp_obj)

        messages.success(request,'OTP sent to email') 
        return redirect('verify_otp')
    
    return render(request,'accounts/signup.html')

    
       

    


        user = User.objects.create_user(
            username=email,  
            email=email,
            password=password
        )

        user.first_name = full_name
        user.save()


        login(request, user)

        return redirect("home") 

    return render(request, "signup.html")