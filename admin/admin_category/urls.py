from django.urls import path
from . import views

urlpatterns = [
    path("category-management/", views.admincategory_view, name="admincategory_view"),
    path("add-category/", views.add_category, name="add_category"),
    path("edit-category/<int:id>/", views.edit_category, name="edit_category"),
    path("delete-category/<int:id>/", views.delete_category, name="delete_category"),
    path(
        "toggle-category-status/<int:id>/",
        views.toggle_category_status,
        name="toggle_category_status",
    ),
]
