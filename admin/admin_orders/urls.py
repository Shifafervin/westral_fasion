from django.urls import path
from . import views

urlpatterns = [
    path("order-management/", views.order_management, name="order_management"),
    path(
        "order-detail/<str:order_id>/",
        views.admin_order_detail,
        name="admin_order_detail",
    ),
    path(
        "update-order-status/<str:order_id>/",
        views.update_order_status,
        name="update_order_status",
    ),
    path("return-management/", views.return_management, name="return_management"),
    path(
        "approve-return/<int:return_id>/", views.approve_return, name="approve_return"
    ),
    path("reject-return/<int:return_id>/", views.reject_return, name="reject_return"),
]
