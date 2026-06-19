from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    
    path("admin/", admin.site.urls),
    path("", include("user.accounts.urls")),
    path("profile/", include("user.user_details.urls")),
    path("address/", include("user.address_details.urls")),
    path("products/", include("user.user_products.urls")),
    path("orders/", include("user.user_orders.urls")),
    path("payments/", include("user.user_payments.urls")),
    path("admin-auth/", include("admin.admin_auth.urls")),
    path("admin-category/", include("admin.admin_category.urls")),
    path("admin-product/", include("admin.admin_product.urls")),
    path("admin-orders/", include("admin.admin_orders.urls")),
    path("admin_coupon/", include("admin.admin_coupon.urls")),
    path("admin-offers/", include("admin.admin_offers.urls")),
    path("accounts/", include("allauth.urls")),
    
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
