from django.urls import path

from . import views

urlpatterns = [
    path("shop/", views.shop, name="shop"),
    path(
        "toggle-wishlist/<int:variant_id>/",
        views.toggle_wishlist,
        name="toggle_wishlist",
    ),
    path(
        "product-details/<int:product_id>/",
        views.product_details,
        name="product_details",
    ),
    path("cart/", views.cart_page, name="cart"),
    path("add-to-cart/<int:variant_id>/", views.add_to_cart, name="add_to_cart"),
    path(
        "cart/increment/<int:item_id>/",
        views.increment_cart_item,
        name="increment_cart_item",
    ),
    path(
        "cart/decrement/<int:item_id>/",
        views.decrement_cart_item,
        name="decrement_cart_item",
    ),
    path("remove/<int:item_id>/", views.remove_cart_item, name="remove_cart_item"),
    path(
        "add-to-wishlist/<int:variant_id>/",
        views.add_to_wishlist,
        name="add_to_wishlist",
    ),
    path("wishlist/", views.wishlist_page, name="wishlist"),
    path(
        "remove-wishlist-item/<int:item_id>/",
        views.remove_wishlist_item,
        name="remove_wishlist_item",
    ),
    path(
    "review/add/<int:product_id>/",
    views.add_review,
    name="add_review",
),
# path(
#     "review/edit/<int:review_id>/",
#     views.edit_review,
#     name="edit_review",
# ),

path(
    "review/delete/<int:review_id>/",
    views.delete_review,
    name="delete_review",
),
]
