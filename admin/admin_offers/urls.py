from django.urls import path
from . import views

urlpatterns = [
    path("offers/", views.offer_list, name="offer_list"),
    path("add-offer/", views.add_offer, name="add_offer"),
    path("edit-offer/<int:offer_id>/", views.edit_offer, name="edit_offer"),
    path("activate-offer/<int:offer_id>/", views.activate_offer, name="activate_offer"),
    path(
        "deactivate-offer/<int:offer_id>/",
        views.deactivate_offer,
        name="deactivate_offer",
    ),
    path("delete-offer/<int:offer_id>/", views.delete_offer, name="delete_offer"),
]
