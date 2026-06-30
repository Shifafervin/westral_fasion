from django.urls import path
from . import views
from django.conf.urls import handler404


urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("signup-verify/", views.signup_verify, name="signup_verify"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("resend-otp/", views.resend_otp, name="resend_otp"),
    path("reset-password/", views.reset_password, name="reset_password"),
    path("search/", views.navbar_search, name="navbar_search"),
    path("referral/", views.referral_page, name="referral_page"),
    path("signup-resend-otp/", views.signup_resend_otp, name="signup_resend_otp"),
    path("about/", views.about_view, name="about"),
    path("contact/", views.contact_view, name="contact"),
    path("privacy-policy/", views.privacy_view, name="privacy_policy"),
    path("terms-conditions/", views.terms_view, name="terms_conditions"),
    path("refund-policy/", views.refund_view, name="refund_policy"),
    path("shipping-policy/", views.shipping_view, name="shipping_policy"),
]

handler404 = "westral_fasion.views.custom_404"