from django.urls import path
from . import views

app_name = "user_details"

urlpatterns = [
    path('', views.profile_page, name='profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('logout/', views.logout_view, name='logout'),
    path('logout-confirm/', views.logout_confirm, name='logout_confirm'),
    path('profile-forgot-password/', views.profile_forgotpassword, name='profile_forgotpassword'),
    path('profile-verify-otp/', views.profile_verify_otp, name='profileverify_otp'),
    path('profile-resend-otp/', views.profile_resend_otp, name='profile_resend_otp'),
    path('profile-reset-password/', views.profile_resetpassword, name='profilereset_password'),
    path("verify-email-otp/", views.verify_email_otp, name="verify_email_otp"),
    path("resend-email-otp/", views.resend_email_otp, name="resend_email_otp"),
]