from django.urls import path
from . import views

app_name = "address_details"

urlpatterns = [
    path('', views.address_page, name='address_view'),   # 🔥 EMPTY
    path('add/', views.add_address, name='add_address'),
    path('delete/<int:id>/', views.delete_address, name='delete_address'),
    path('edit/<int:id>/', views.edit_address, name='edit_address'),
]
