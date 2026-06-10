from django.urls import path

from . import views

urlpatterns = [
    path("product-management/", views.product_management, name="product_management"),
    path("add-product/", views.add_product, name="add_product"),
    path("edit-product/<int:id>/", views.edit_product, name="edit_product"),
    path("delete-product/<int:id>/", views.delete_product, name="delete_product"),
    path(
        "toggle-product-status/<int:id>/",
        views.toggle_product_status,
        name="toggle_product_status",
    ),
    path(
        "variants/<int:product_id>/",
        views.variant_management,
        name="variant_management",
    ),
    path("variant/edit/<int:variant_id>/", views.edit_variant, name="edit_variant"),
    path("variant/add/<int:product_id>/", views.add_variant, name="add_variant"),
    path(
        "delete-variant/<int:variant_id>/",
        views.delete_variant_page,
        name="delete_variant_page",
    ),
]
